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
        BATCH_SIZE = 1000
        
        self.stdout.write(self.style.SUCCESS(f'Начало заполнения БД с коэффициентом: {ratio}'))

        # --- 1. Пользователи ---
        self.stdout.write('1/6. Генерация пользователей...')
        hashed_pw = make_password('test123')
        
        users_to_create = []
        unique_emails = []
        
        for i in range(1, ratio + 1):
            email = f'user{i}@example.com'
            unique_emails.append(email)
            users_to_create.append(User(
                email=email,
                username=f'tech_user_{i}_{fake.unique.word()}', # Уникальный username для безопасности
                password=hashed_pw,
                is_active=True
            ))
        
        # Создаем пользователей
        User.objects.bulk_create(users_to_create, batch_size=BATCH_SIZE, ignore_conflicts=True)
        
        # Получаем реальные объекты из БД, чтобы знать их ID
        created_users = User.objects.filter(email__in=unique_emails).order_by('id')
        user_ids = list(created_users.values_list('id', flat=True))
        
        if not user_ids:
            self.stdout.write(self.style.ERROR('Не удалось создать пользователей. Проверьте БД.'))
            return

        self.stdout.write(f'   Создано {len(user_ids)} пользователей.')

        # --- 2. Профили ---
        self.stdout.write('2/6. Генерация профилей...')
        profiles_to_create = []
        
        # Генерируем уникальные никнеймы заранее
        nicknames = [f"{fake.user_name()}_{i}" for i in range(len(user_ids))]
        
        for idx, uid in enumerate(user_ids):
            profiles_to_create.append(Profile(
                user_id=uid,
                nickname=nicknames[idx],
                bio=fake.text(max_nb_chars=200)
            ))
            
        Profile.objects.bulk_create(profiles_to_create, batch_size=BATCH_SIZE, ignore_conflicts=True)
        self.stdout.write(f'   Создано {len(profiles_to_create)} профилей.')

        # --- 3. Теги ---
        self.stdout.write('3/6. Генерация тегов...')
        tag_count = min(ratio, 50) # Ограничим количество тегов, чтобы не было каши
        tag_names = [f'tag_{fake.word()[:8]}' for _ in range(tag_count)]
        
        tags_to_create = [Tag(name=name) for name in tag_names]
        Tag.objects.bulk_create(tags_to_create, batch_size=BATCH_SIZE, ignore_conflicts=True)
        
        # Получаем ID созданных тегов
        tag_ids = list(Tag.objects.filter(name__in=tag_names).values_list('pk', flat=True))
        self.stdout.write(f'   Создано {len(tag_ids)} тегов.')

        # --- 4. Вопросы ---
        questions_count = ratio * 5
        self.stdout.write(f'4/6. Генерация {questions_count} вопросов...')
        
        questions_to_create = []
        for _ in range(questions_count):
            questions_to_create.append(Question(
                title=fake.sentence(nb_words=6),
                text=fake.paragraph(nb_sentences=3),
                author_id=random.choice(user_ids)
            ))
            
        Question.objects.bulk_create(questions_to_create, batch_size=BATCH_SIZE)
        
        # Получаем ID созданных вопросов
        question_ids = list(Question.objects.order_by('-id').values_list('pk', flat=True)[:questions_count])
        self.stdout.write(f'   Создано {len(question_ids)} вопросов.')

        # --- 5. Связь Вопрос-Тег (M2M) ---
        self.stdout.write('5/6. Привязка тегов к вопросам...')
        if tag_ids and question_ids:
            m2m_model = Question.tags.through
            m2m_batch = []
            
            for q_id in question_ids:
                # Каждый вопрос получает от 1 до 3 тегов
                num_tags = random.randint(1, min(3, len(tag_ids)))
                selected_tags = random.sample(tag_ids, num_tags)
                for t_id in selected_tags:
                    m2m_batch.append(m2m_model(question_id=q_id, tag_id=t_id))
                
                if len(m2m_batch) >= BATCH_SIZE:
                    m2m_model.objects.bulk_create(m2m_batch, ignore_conflicts=True)
                    m2m_batch = []
                    
            if m2m_batch:
                m2m_model.objects.bulk_create(m2m_batch, ignore_conflicts=True)
        
        self.stdout.write('   Привязка тегов завершена.')

        # --- 6. Ответы ---
        answers_count = ratio * 10
        self.stdout.write(f'6/6. Генерация {answers_count} ответов...')
        
        answers_to_create = []
        for _ in range(answers_count):
            answers_to_create.append(Answer(
                question_id=random.choice(question_ids),
                author_id=random.choice(user_ids),
                text=fake.paragraph(nb_sentences=2),
                is_correct=random.choices([True, False], weights=[10, 90])[0]
            ))
            
        Answer.objects.bulk_create(answers_to_create, batch_size=BATCH_SIZE)
        self.stdout.write(f'   Создано {len(answers_to_create)} ответов.')

        self.stdout.write(self.style.SUCCESS('\nБаза данных успешно заполнена!'))
        