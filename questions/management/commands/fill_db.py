import random
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from faker import Faker
from questions.models import Tag, Profile, Question, Answer, QuestionLike, AnswerLike

User = get_user_model()

class Command(BaseCommand):
    help = 'Эффективно заполняет БД тестовыми данными. Использование: python manage.py fill_db <ratio>'

    def add_arguments(self, parser):
        parser.add_argument('ratio', type=int, help='Коэффициент масштабирования генерации данных')

    def handle(self, *args, **options):
        ratio = options['ratio']
        fake = Faker('ru_RU')
        BATCH_SIZE = 10000

        self.stdout.write(self.style.SUCCESS(f'Начало заполнения БД с коэффициентом: {ratio}'))

        # 1. Пользователи + Профили
        self.stdout.write('1/7. Генерация пользователей и профилей...')
        hashed_pw = make_password('test123')
        
        users = []
        profiles = []
        
        generated_nicknames = [f"{fake.user_name()}_{i}" for i in range(ratio)]
        
        for i in range(1, ratio + 1):
            email = f'user{i}@example.com'
            
            user = User(
                email=email,
                username=f'tech_user_{i}',
                password=hashed_pw,
                is_active=True
            )
            users.append(user)
            
            profile = Profile(
                user_id=None,
                nickname=generated_nicknames[i-1],
                bio=fake.text(max_nb_chars=250)
            )
            profiles.append(profile)
        
        User.objects.bulk_create(users, batch_size=BATCH_SIZE, ignore_conflicts=True)
        
        created_users = User.objects.filter(
            email__in=[f'user{i}@example.com' for i in range(1, ratio + 1)]
        ).order_by('id')
        
        user_ids = [u.pk for u in created_users]
        
        for idx, profile in enumerate(profiles):
            if idx < len(user_ids):
                profile.user_id = user_ids[idx]
        
        Profile.objects.bulk_create(profiles, batch_size=BATCH_SIZE, ignore_conflicts=True)
        
        self.stdout.write(f'Создано {len(user_ids)} пользователей с профилями')

        # 2. Теги
        self.stdout.write('2/7. Генерация тегов...')
        tag_names = [f'tag_{i}_{fake.word()[:6]}' for i in range(1, ratio + 1)]
        tags = [Tag(name=name) for name in tag_names]
        Tag.objects.bulk_create(tags, batch_size=BATCH_SIZE, ignore_conflicts=True)
        
        tag_ids = list(Tag.objects.filter(name__in=tag_names).values_list('pk', flat=True))
        self.stdout.write(f'Создано {len(tag_ids)} тегов')

        # 3. Вопросы
        questions_count = ratio * 10
        self.stdout.write(f'3/7. Генерация {questions_count} вопросов...')
        
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
        
        question_ids = [q.pk for q in created_questions if q.pk]
        self.stdout.write(f'Создано {len(question_ids)} вопросов')

        # 4. Связь Вопрос-Тег (M2M)
        self.stdout.write('4/7. Привязка тегов к вопросам...')
        if tag_ids and question_ids:
            m2m_model = Question.tags.through
            m2m_batch = []
            
            for q_id in question_ids:
                num_tags = random.randint(1, min(5, len(tag_ids)))
                selected_tags = random.sample(tag_ids, num_tags)
                for t_id in selected_tags:
                    m2m_batch.append(m2m_model(question_id=q_id, tag_id=t_id))
                    if len(m2m_batch) >= BATCH_SIZE:
                        m2m_model.objects.bulk_create(m2m_batch, ignore_conflicts=True)
                        m2m_batch = []
            if m2m_batch:
                m2m_model.objects.bulk_create(m2m_batch, ignore_conflicts=True)
        
        self.stdout.write('Привязка тегов завершена')

        # 5. Ответы
        answers_count = ratio * 100
        self.stdout.write(f'5/7. Генерация {answers_count} ответов...')
        
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
        
        answer_ids = [a.pk for a in created_answers if a.pk]
        self.stdout.write(f'Создано {len(answer_ids)} ответов')

        # 6. Лайки (Вопросы + Ответы)
        likes_count = ratio * 100
        self.stdout.write(f'6/7. Генерация {likes_count * 2} лайков...')

        # Лайки вопросов
        if user_ids and question_ids:
            q_like_batch = []
            for _ in range(likes_count):
                q_like_batch.append(QuestionLike(
                    user_id=random.choice(user_ids),
                    question_id=random.choice(question_ids)
                ))
                if len(q_like_batch) >= BATCH_SIZE:
                    QuestionLike.objects.bulk_create(q_like_batch, ignore_conflicts=True)
                    q_like_batch = []
            if q_like_batch:
                QuestionLike.objects.bulk_create(q_like_batch, ignore_conflicts=True)

        # Лайки ответов
        if user_ids and answer_ids:
            a_like_batch = []
            for _ in range(likes_count):
                a_like_batch.append(AnswerLike(
                    user_id=random.choice(user_ids),
                    answer_id=random.choice(answer_ids)
                ))
                if len(a_like_batch) >= BATCH_SIZE:
                    AnswerLike.objects.bulk_create(a_like_batch, ignore_conflicts=True)
                    a_like_batch = []
            if a_like_batch:
                AnswerLike.objects.bulk_create(a_like_batch, ignore_conflicts=True)

        self.stdout.write(self.style.SUCCESS('\nБаза данных успешно заполнена!'))
