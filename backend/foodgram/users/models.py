from django.contrib.auth import get_user_model
from django.db import models


CustomUser = get_user_model()


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
