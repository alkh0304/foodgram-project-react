from django.contrib.auth.models import AbstractUser
from django.core.validators import MinLengthValidator
from django.db import models
from django.utils import timezone


class CustomUser(AbstractUser):
    """Кастомная модель пользователя основанная на AbstractUser."""
    username = models.CharField(
        'Имя пользователя', max_length=150, unique=True,
        validators=[MinLengthValidator(5, message='Минимум 5 символов')])
    password = models.CharField(
        'Пароль', max_length=150,
        validators=[MinLengthValidator(5, message='Минимум 5 символов')])
    email = models.EmailField('Email адрес', unique=True)
    first_name = models.CharField('Имя', max_length=30, blank=True)
    last_name = models.CharField('Фамилия', max_length=150, blank=True)
    date_joined = models.DateTimeField('Дата создания', default=timezone.now)
    bio = models.CharField('Биография', max_length=200, blank=True, default=1)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = [
        'first_name', 'last_name', 'password'
        ]

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        ordering = ('username',)
        constraints = [
            models.UniqueConstraint(fields=[
                'username',
                'email'
            ], name='unique_user'),
        ]

    def __str__(self):
        return f'{self.username}'


class Subscription(models.Model):
    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='subscriber',
        verbose_name='подписчик'
    )
    author = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='author',
        verbose_name='Автор'
    )

    class Meta:
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'
        constraints = [
            models.UniqueConstraint(fields=['user', 'author'],
                                    name='unique_subscription')
        ]

    def __str__(self):
        return f'{self.user} подписался на {self.author}'
