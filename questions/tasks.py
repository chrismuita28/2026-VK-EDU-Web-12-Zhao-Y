from celery import shared_task
from django.core.cache import cache
from django.db.models import Count, Q
from django.utils import timezone
from datetime import timedelta
from django.conf import settings
from django.contrib.auth import get_user_model
from questions.models import Tag, Question, Answer, Profile
from collections import defaultdict
import requests

User = get_user_model()

CACHE_KEYS = {
    'popular_tags': 'sidebar:popular_tags',
    'best_users': 'sidebar:best_users',
}
CACHE_TIMEOUT = 3600
FALLBACK_TIMEOUT = 300


def _calculate_popular_tags_from_db():
    """Внутренняя функция: топ-10 тегов по количеству вопросов за 3 месяца"""
    three_months_ago = timezone.now() - timedelta(days=90)
    
    tags = Tag.objects.annotate(
        question_count=Count(
            'questions',
            filter=Q(questions__created_at__gte=three_months_ago)
        )
    ).filter(
        question_count__gt=0
    ).order_by(
        '-question_count', 'name'
    ).values('id', 'name', 'question_count')[:10]
    
    return list(tags)


def _calculate_best_users_from_db():
    """Внутренняя функция: топ-10 пользователей по популярности вопросов/ответов за неделю"""
    one_week_ago = timezone.now() - timedelta(days=7)
    
    question_scores = Question.objects.filter(
        created_at__gte=one_week_ago
    ).annotate(
        likes_count=Count('likes')
    ).values('author_id').annotate(
        total=Count('likes')
    ).values('author_id', 'total')
    
    answer_scores = Answer.objects.filter(
        created_at__gte=one_week_ago
    ).annotate(
        likes_count=Count('likes')
    ).values('author_id').annotate(
        total=Count('likes')
    ).values('author_id', 'total')
    
    user_scores = defaultdict(int)
    for item in question_scores:
        user_scores[item['author_id']] += item['total'] + 1
    for item in answer_scores:
        user_scores[item['author_id']] += item['total'] + 1
    
    if not user_scores:
        return []
    
    top_user_ids = sorted(user_scores.keys(), key=lambda x: user_scores[x], reverse=True)[:10]
    profiles = Profile.objects.select_related('user').filter(user_id__in=top_user_ids)
    profile_map = {p.user.pk: p for p in profiles}
    
    result = []
    for uid in top_user_ids:
        profile = profile_map.get(uid)
        if profile:
            result.append({
                'id': profile.user.pk,
                'nickname': profile.nickname or profile.user.email,
                'email': profile.user.email,
                'avatar': profile.avatar.url if profile.avatar else None,
                'score': user_scores[uid]
            })
    
    return result


@shared_task(name='questions.calculate_popular_tags')
def calculate_popular_tags():
    data = _calculate_popular_tags_from_db()
    cache.set(CACHE_KEYS['popular_tags'], data, CACHE_TIMEOUT)
    return {'status': 'ok', 'count': len(data)}


@shared_task(name='questions.calculate_best_users')
def calculate_best_users():
    data = _calculate_best_users_from_db()
    cache.set(CACHE_KEYS['best_users'], data, CACHE_TIMEOUT)
    return {'status': 'ok', 'count': len(data)}


def get_cached_popular_tags():
    data = cache.get(CACHE_KEYS['popular_tags'])
    if data is None:
        data = _calculate_popular_tags_from_db()
        cache.set(CACHE_KEYS['popular_tags'], data, FALLBACK_TIMEOUT)
    return data


def get_cached_best_users():
    data = cache.get(CACHE_KEYS['best_users'])
    if data is None:
        data = _calculate_best_users_from_db()
        cache.set(CACHE_KEYS['best_users'], data, FALLBACK_TIMEOUT)
    return data

import logging
logger = logging.getLogger(__name__)

@shared_task(name='questions.notify_new_answer')
def notify_new_answer(question_id, answer_data):
    channel = f"{settings.CENTRIFUGO_NAMESPACE}:question:{question_id}"
    url = f"{settings.CENTRIFUGO_URL}/api"
    
    headers = {
        "Authorization": f"apikey {settings.CENTRIFUGO_API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "method": "publish",
        "params": {
            "channel": channel,
            "data": answer_data
        }
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=5)
        response.raise_for_status()
        logger.info(f"Published to {channel}: {response.json()}")
    except requests.RequestException as e:
        logger.error(f"Failed to publish to Centrifugo: {e}")
        raise
