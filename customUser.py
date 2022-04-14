from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.utils.translation import gettext_lazy as _
from django.core.validators import FileExtensionValidator
from base.services import validate_photo_size, get_image_upload
from base.choices import Sex
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from django.contrib.auth.base_user import BaseUserManager


"""
Модель кастомного пользователя. В качестве примера для разбора была взята задача:
Пользователь аутентифицируется по сочетанию логина и пароля. В качестве логина используется емейл.
У пользователя может быть несколько дополнительных емейлов. При этом все емейлы в системе уникальные.
"""


class CustomUserManager(BaseUserManager):
    """
    Менеджер кастомной модели пользователи CustomUser.
    """

    def create_user(self, password, email='', **extra_fields):
        """
        Создание экземпляра модели CustomUser и сохранение в БД, при этом автоматически создается
        связанная модель профиля.
        """
        if email == '':
            raise ValidationError(_('The email must be set'))
        extra_fields.setdefault('is_active', True)
        extra_fields.setdefault('is_superuser', False)
        try:
            email = self.normalize_email(email.lower())
        except ValueError:
            raise ValidationError(_('email is not valid'))
        if UserAdditionalEmail.objects.filter(email=email).exists() or \
                self.model.objects.filter(email=email).exists():
            raise ValidationError(_('email is already in use in the system'))
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save()
        profile = Profile(user=user)
        profile.save()
        return user

    def create_superuser(self, email, password, **extra_fields):
        """
        Создание экземпляра модели SuperUser и сохранение в БД с закодированным паролем.
        """
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        return self.create_user(password, email, **extra_fields)


class CustomUser(AbstractBaseUser, PermissionsMixin):
    """
    Кастомная модель пользователя.
    Здесь храним информацию, связанную со входом в систему.
    """
    email = models.EmailField(_('email address'), blank=False, null=False)
    isActive = models.BooleanField(_('is active'), default=True)
    dateJoined = models.DateTimeField(_('joining date'), auto_now_add=True, editable=False)
    lastLogin = models.DateTimeField(_('last entrance'), editable=False)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['email']

    # objects = CustomUserManager()

    class Meta:
        verbose_name = _('user')
        verbose_name_plural = _('users')

    def __str__(self):
        return self.email


User = get_user_model()


class UserAdditionalEmail(models.Model):
    """
    Дополнительные емейлы пользователя.
    """
    email = models.EmailField(_('email'), unique=True, null=False, blank=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=False, blank=False,
                             related_name='additional_emails')

    class Meta:
        verbose_name = _('email')
        verbose_name_plural = _('emails')

    def __str__(self):
        return self.email

    def clean(self, *args, **kwargs):
        user_manager = BaseUserManager()
        try:
            self.email = user_manager.normalize_email(self.email.lower())
        except ValueError:
            raise ValidationError(_('email is not valid'))
        if CustomUser.objects.filter(email=self.email).exists() or \
                self.model.objects.filter(email=self.email).exists():
            raise ValidationError('email is already in use in the system')
        else:
            super(UserAdditionalEmail, self).clean()


class Profile(models.Model):
    """
    Модель профиля пользователя. Вся расширенная информация о пользователе хранится здесь.
    """
    name = models.CharField(_('name'), max_length=50, blank=True, null=False)
    surname = models.CharField(_('surname'), max_length=50, blank=True, null=False)
    patronymic = models.CharField(_('patronymic'), max_length=50, blank=True, null=False)
    birthdate = models.DateField(_('age'), null=True, blank=True)
    sex = models.CharField(max_length=1, choices=Sex.sex_choices, default=Sex.MALE, null=False)
    photo = models.ImageField(
        _('photo'),
        upload_to=get_image_upload,
        blank=True,
        null=True,
        validators=[FileExtensionValidator(allowed_extensions=['jpg', 'png', 'jpeg']), validate_photo_size]
    )
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        blank=False, null=False,
        related_name='users'
    )

    class Meta:
        verbose_name = _('profile')
        verbose_name_plural = _('profiles')

    def __str__(self):
        if self.name and self.surname:
            return '{} {}'.format(self.name, self.surname)
        elif self.name:
            return '{}'.format(self.name)
        elif self.surname:
            return '{}'.format(self.surname)
        else:
            return '{}'.format(self.user.email)



