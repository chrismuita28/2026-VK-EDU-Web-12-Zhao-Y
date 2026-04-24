import random
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password
from faker import Faker
from questions.models import Tag, Profile, Question, Answer, QuestionLike, AnswerLike

class Command(BaseCommand):
    help = 'Эффективно заполняет БД тестовыми данными. Использование: python manage.py fill_db <ratio>'

    def add_arguments(self, parser):
        parser.add_argument('ratio', type=int, help='Коэффициент масштабирования генерации данных')

    def handle(self, *args, **options):
        ratio = options['ratio']
        fake = Faker('ru_RU')
        BATCH_SIZE = 10000

        self.stdout.write(self.style.SUCCESS(f'Начало заполнения БД с коэффициентом: {ratio}'))

        # 1. Пользователи
        self.stdout.write('1/7. Генерация пользователей...')
        hashed_pw = make_password('test123')
        users = [
            User(username=f'user_{i}_{fake.word()[:5]}', password=hashed_pw, email=f'user{i}@example.com')
            for i in range(1, ratio + 1)
        ]
        User.objects.bulk_create(users, batch_size=BATCH_SIZE)
        user_ids = [u.pk for u in users if u.pk]
        self.stdout.write(f'Создано {len(user_ids)} пользователей')

        # 2. Профили
        self.stdout.write('2/7. Генерация профилей...')
        user_usernames = {u.pk: u.username for u in User.objects.filter(pk__in=user_ids).only('pk', 'username')}
        profiles = [
            Profile(
                user_id=uid, 
                nickname=user_usernames.get(uid, f'user_{uid}'),
                bio=fake.text(max_nb_chars=250)
            ) 
            for uid in user_ids
        ]
        Profile.objects.bulk_create(profiles, batch_size=BATCH_SIZE)
        self.stdout.write(f'Создано {len(profiles)} профилей')

        # 3. Теги
        self.stdout.write('3/7. Генерация тегов...')
        tags = [Tag(name=f'tag_{i}_{fake.word()[:6]}') for i in range(1, ratio + 1)]
        Tag.objects.bulk_create(tags, batch_size=BATCH_SIZE)
        tag_ids = [t.pk for t in tags if t.pk]
        self.stdout.write(f'Создано {len(tag_ids)} тегов')

        # 4. Вопросы
        questions_count = ratio * 10
        self.stdout.write(f'4/7. Генерация {questions_count} вопросов...')
        created_questions = []
        batch = []
        for _ in range(questions_count):
            batch.append(Question(
                title=fake.sentence(nb_words=6),
                text=fake.text(max_nb_chars=500),
                author_id=random.choice(user_ids)
            ))
            if len(batch) >= BATCH_SIZE:
                Question.objects.bulk_create(batch)
                created_questions.extend(batch)
                batch = []
        if batch:
            Question.objects.bulk_create(batch)
            created_questions.extend(batch)
        question_ids = [q.pk for q in created_questions]
        self.stdout.write(f'Создано {len(question_ids)} вопросов')

        # 5. Связь Вопрос-Тег (M2M)
        self.stdout.write('5/7. Привязка тегов к вопросам...')
        m2m_model = Question.tags.through
        m2m_batch = []
        for q_id in question_ids:
            num_tags = random.randint(1, 5)
            selected_tags = random.sample(tag_ids, min(num_tags, len(tag_ids)))
            for t_id in selected_tags:
                m2m_batch.append(m2m_model(question_id=q_id, tag_id=t_id))
                if len(m2m_batch) >= BATCH_SIZE:
                    m2m_model.objects.bulk_create(m2m_batch)
                    m2m_batch = []
        if m2m_batch:
            m2m_model.objects.bulk_create(m2m_batch)
        self.stdout.write('Привязка завершена')

        # 6. Ответы
        answers_count = ratio * 100
        self.stdout.write(f'6/7. Генерация {answers_count} ответов...')
        created_answers = []
        batch = []
        for _ in range(answers_count):
            batch.append(Answer(
                question_id=random.choice(question_ids),
                author_id=random.choice(user_ids),
                text=fake.text(max_nb_chars=400),
                is_correct=random.choices([True, False], weights=[5, 95])[0]
            ))
            if len(batch) >= BATCH_SIZE:
                Answer.objects.bulk_create(batch)
                created_answers.extend(batch)
                batch = []
        if batch:
            Answer.objects.bulk_create(batch)
            created_answers.extend(batch)
        answer_ids = [a.pk for a in created_answers]
        self.stdout.write(f'Создано {len(answer_ids)} ответов')

        # 7. Лайки (Вопросы + Ответы)
        likes_count = ratio * 100
        self.stdout.write(f'7/7. Генерация {likes_count * 2} лайков...')

        # Лайки вопросов
        q_like_batch = []
        for _ in range(likes_count):
            q_like_batch.append(QuestionLike(
                user_id=random.choice(user_ids),
                question_id=random.choice(question_ids)
            ))
            if len(q_like_batch) >= BATCH_SIZE:
                QuestionLike.objects.bulk_create(q_like_batch)
                q_like_batch = []
        if q_like_batch:
            QuestionLike.objects.bulk_create(q_like_batch)

        # Лайки ответов
        a_like_batch = []
        for _ in range(likes_count):
            a_like_batch.append(AnswerLike(
                user_id=random.choice(user_ids),
                answer_id=random.choice(answer_ids)
            ))
            if len(a_like_batch) >= BATCH_SIZE:
                AnswerLike.objects.bulk_create(a_like_batch)
                a_like_batch = []
        if a_like_batch:
            AnswerLike.objects.bulk_create(a_like_batch)

        self.stdout.write(self.style.SUCCESS('\nБаза данных успешно заполнена тестовыми данными!'))
