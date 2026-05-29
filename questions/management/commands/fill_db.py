import random
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from faker import Faker
from questions.models import Tag, Profile, Question, Answer, QuestionLike, AnswerLike

User = get_user_model()

class Command(BaseCommand):
    BATCH_SIZE = 1000

    def add_arguments(self, parser):
        parser.add_argument('ratio', type=int)

    def handle(self, *args, **options):
        ratio = options['ratio']
        self.fake = Faker('ru_RU')
        
        self.stdout.write(self.style.SUCCESS(f'Начало заполнения БД с коэффициентом: {ratio}'))

        user_ids = self._create_users(ratio)
        if not user_ids:
            self.stdout.write(self.style.ERROR('Не удалось создать пользователей. Прерывание.'))
            return

        self._create_profiles(user_ids)
        tag_ids = self._create_tags(ratio)
        question_ids = self._create_questions(ratio, user_ids)
        
        if tag_ids and question_ids:
            self._attach_tags_to_questions(question_ids, tag_ids)
        
        answer_ids = self._create_answers(ratio, question_ids, user_ids)
        
        self._create_question_likes(ratio, question_ids, user_ids)
        
        self.stdout.write(self.style.SUCCESS('\nБаза данных успешно заполнена!'))
        self.stdout.write(self.style.SUCCESS(
            f'Создано: {ratio} пользователей, {ratio * 10} вопросов, '
            f'{ratio * 100} ответов, {ratio} тегов, {ratio * 200} оценок'
        ))

    def _get_created_ids(self, model, filter_field, values, order_by='-id', limit=None):
        qs = model.objects.filter(**{f'{filter_field}__in': values}).order_by(order_by)
        if limit:
            qs = qs[:limit]
        return list(qs.values_list('pk', flat=True))

    def _bulk_create_with_ids(self, model, objects, id_field, batch_size=None):
        batch_size = batch_size or self.BATCH_SIZE
        model.objects.bulk_create(objects, batch_size=batch_size, ignore_conflicts=True)
        values = [getattr(obj, id_field) for obj in objects]
        return self._get_created_ids(model, id_field, values, limit=len(objects))

    def _create_users(self, ratio):
        self.stdout.write('1/7. Генерация пользователей...')
        hashed_pw = make_password('test123')
        
        users = [
            User(
                email=f'user{i}@example.com',
                username=f'tech_user_{i}_{self.fake.unique.word()}',
                password=hashed_pw,
                is_active=True
            )
            for i in range(1, ratio + 1)
        ]
        
        return self._bulk_create_with_ids(User, users, 'email')

    def _create_profiles(self, user_ids):
        self.stdout.write('2/7. Генерация профилей...')
        
        nicknames = [f"{self.fake.user_name()}_{i}" for i in range(len(user_ids))]
        profiles = [
            Profile(user_id=uid, nickname=nicknames[idx], bio=self.fake.text(max_nb_chars=200))
            for idx, uid in enumerate(user_ids)
        ]
        
        Profile.objects.bulk_create(profiles, batch_size=self.BATCH_SIZE, ignore_conflicts=True)
        self.stdout.write(f'   Создано {len(profiles)} профилей.')

    def _create_tags(self, ratio):
        self.stdout.write('3/7. Генерация тегов...')
        tag_names = [f'tag_{self.fake.word()[:8]}_{i}' for i in range(ratio)]
        
        tags = [Tag(name=name) for name in tag_names]
        return self._bulk_create_with_ids(Tag, tags, 'name')

    def _create_questions(self, ratio, user_ids):
        count = ratio * 10
        self.stdout.write(f'4/7. Генерация {count} вопросов...')
        
        questions = [
            Question(
                title=self.fake.sentence(nb_words=6),
                text=self.fake.paragraph(nb_sentences=3),
                author_id=random.choice(user_ids)
            )
            for _ in range(count)
        ]
        
        Question.objects.bulk_create(questions, batch_size=self.BATCH_SIZE)
        return list(Question.objects.order_by('-id').values_list('pk', flat=True)[:count])

    def _attach_tags_to_questions(self, question_ids, tag_ids):
        self.stdout.write('5/7. Привязка тегов к вопросам...')
        m2m_model = Question.tags.through
        batch = []
        
        for q_id in question_ids:
            num_tags = random.randint(1, min(3, len(tag_ids)))
            for t_id in random.sample(tag_ids, num_tags):
                batch.append(m2m_model(question_id=q_id, tag_id=t_id))
            
            if len(batch) >= self.BATCH_SIZE:
                m2m_model.objects.bulk_create(batch, ignore_conflicts=True)
                batch = []
        
        if batch:
            m2m_model.objects.bulk_create(batch, ignore_conflicts=True)
        
        self.stdout.write('   Привязка тегов завершена.')

    def _create_answers(self, ratio, question_ids, user_ids):
        count = ratio * 100
        self.stdout.write(f'6/7. Генерация {count} ответов...')
        
        answers = [
            Answer(
                question_id=random.choice(question_ids),
                author_id=random.choice(user_ids),
                text=self.fake.paragraph(nb_sentences=2),
                is_correct=random.choices([True, False], weights=[10, 90])[0]
            )
            for _ in range(count)
        ]
        
        Answer.objects.bulk_create(answers, batch_size=self.BATCH_SIZE)
        return list(Answer.objects.order_by('-id').values_list('pk', flat=True)[:count])

    def _create_question_likes(self, ratio, question_ids, user_ids):
        """Генерация оценок пользователей (лайков к вопросам) - ratio * 200"""
        count = ratio * 200
        if not question_ids or not user_ids:
            return
            
        self.stdout.write(f'7/7. Генерация {count} оценок (лайков)...')
        
        created_pairs = set()
        likes = []
        attempts = 0
        max_attempts = count * 3
        
        while len(likes) < count and attempts < max_attempts:
            user_id = random.choice(user_ids)
            question_id = random.choice(question_ids)
            pair = (user_id, question_id)
            
            if pair not in created_pairs:
                created_pairs.add(pair)
                likes.append(QuestionLike(user_id=user_id, question_id=question_id))
            attempts += 1
            
            if len(likes) >= self.BATCH_SIZE:
                QuestionLike.objects.bulk_create(likes, ignore_conflicts=True)
                likes = []
        
        if likes:
            QuestionLike.objects.bulk_create(likes, ignore_conflicts=True)
            
        self.stdout.write(f'   Создано {len(created_pairs)} оценок к вопросам.')
