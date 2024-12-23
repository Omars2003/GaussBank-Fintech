from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.db.models.signals import post_save
from datetime import datetime
from django.db import models
from django.dispatch import receiver


class CustomUser(AbstractUser):
    email = models.EmailField(unique=True)  # Email único como identificador principal

    USERNAME_FIELD = 'email'  # Usa email como identificador principal para el login
    REQUIRED_FIELDS = ['username']  # username será obligatorio al registrarse

    def __str__(self):
        return self.email
# Bank Account Model
class BankAccount(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="bankaccount"
    )
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    total_deposits = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    active_loans = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    def __str__(self):
        return f"{self.user.email}'s Bank Account"

@receiver(post_save, sender=CustomUser)
def create_bank_account(sender, instance, created, **kwargs):
    if created:
        BankAccount.objects.create(user=instance)


################################################################################################################################ GROUP SAVINGS

class GroupSavings(models.Model):
    name = models.CharField(max_length=255)  # Nombre del grupo
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='created_groups'
    )  # Usuario que creó el grupo
    goal_amount = models.DecimalField(max_digits=10, decimal_places=2)  # Meta de ahorro
    weekly_minimum = models.DecimalField(max_digits=10, decimal_places=2)  # Monto mínimo semanal
    created_at = models.DateTimeField(auto_now_add=True)  # Fecha de creación
    description = models.TextField(blank=True, null=True)  # Descripción opcional
    total_contributed = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)  # Total aportado al grupo

    def __str__(self):
        return f"{self.name} (Goal: ${self.goal_amount})"

class GroupParticipation(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='participations'
    )  # Usuario que participa
    group = models.ForeignKey(
        GroupSavings, on_delete=models.CASCADE, related_name='participants'
    )  # Grupo en el que participa
    amount_contributed = models.DecimalField(max_digits=10, decimal_places=2, default=0)  # Aportación total del usuario

    def contribute(self, amount):
        # Validar que el usuario tenga suficiente saldo en Total Deposits
        if self.user.bankaccount.total_deposits < amount:
            raise ValidationError("Insufficient funds in Total Deposits.")
        
        # Deduce el monto de Total Deposits
        self.user.bankaccount.total_deposits -= amount
        self.user.bankaccount.save()

        # Suma el monto al grupo y a la contribución del usuario
        self.amount_contributed += amount
        self.group.total_contributed += amount
        self.save()
        self.group.save()

    def __str__(self):
        return f"{self.user.username} in {self.group.name}"
#########################################################################################################################################
class SavingsChallenge(models.Model):
    name = models.CharField(max_length=255, default="40-Week Savings Challenge")
    weeks = models.PositiveIntegerField(default=40)
    goal_amount = models.DecimalField(max_digits=10, decimal_places=2, default=2000.00)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} - ${self.goal_amount}"

class ChallengeParticipation(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='challenge_participations')
    challenge = models.ForeignKey(SavingsChallenge, on_delete=models.CASCADE, related_name='participations')
    custom_goal_amount = models.DecimalField(max_digits=10, decimal_places=2, default=2000.00)  # Meta personalizada
    total_contributed = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    created_at = models.DateTimeField(auto_now_add=True)

    def weekly_amount(self):
        # Calcula el monto semanal basado en la meta personalizada
        return self.custom_goal_amount / self.challenge.weeks

    def __str__(self):
        return f"{self.user.username} in {self.challenge.name}"

class WeeklyContribution(models.Model):
    participation = models.ForeignKey(ChallengeParticipation, on_delete=models.CASCADE, related_name='weekly_contributions')
    week_number = models.PositiveIntegerField()
    contributed_amount = models.DecimalField(max_digits=10, decimal_places=2)
    contributed_at = models.DateField(auto_now_add=True)

    def __str__(self):
        return f"Week {self.week_number} - ${self.contributed_amount}"
###################################################################################################################### INVESTMENT
class InvestOption(models.Model):
    name = models.CharField(max_length=200, help_text="Name of the investment option")
    description = models.TextField(help_text="Detailed description of the investment option")
    yield_rate = models.DecimalField(max_digits=5, decimal_places=2, help_text="Yield rate as a percentage")
    minimum_investment = models.DecimalField(max_digits=10, decimal_places=2, help_text="Minimum investment amount")
    image = models.ImageField(upload_to='invest_images/', blank=True, null=True, help_text="Optional image for the investment option")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name