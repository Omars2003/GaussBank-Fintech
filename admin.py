from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, BankAccount, GroupSavings, GroupParticipation, SavingsChallenge,InvestOption

# Personalización del modelo de usuario
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'is_staff', 'is_active', 'date_joined')
    list_filter = ('is_staff', 'is_active', 'is_superuser')
    search_fields = ('email', 'username')

    # Configuración para mostrar campos de solo lectura
    readonly_fields = ('created_groups_display', 'participations_display')

    fieldsets = UserAdmin.fieldsets + (
        ('Group Savings Info', {
            'fields': ('created_groups_display', 'participations_display'),
        }),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2'),
        }),
    )

    ordering = ('email',)

    # Métodos para mostrar la información de grupos en el admin
    def created_groups_display(self, obj):
        groups = obj.created_groups.all()
        return ", ".join([group.name for group in groups]) if groups else "No groups created"
    created_groups_display.short_description = "Created Groups"

    def participations_display(self, obj):
        participations = obj.participations.all()
        return ", ".join([participation.group.name for participation in participations]) if participations else "No participations"
    participations_display.short_description = "Participations"

# Personalización del modelo BankAccount
@admin.register(BankAccount)
class BankAccountAdmin(admin.ModelAdmin):
    list_display = ('user', 'balance', 'total_deposits', 'active_loans')
    list_filter = ('balance',)
    search_fields = ('user__email', 'user__username')

# Personalización del modelo GroupSavings
class GroupSavingsAdmin(admin.ModelAdmin):
    list_display = ('name', 'goal_amount', 'weekly_minimum', 'created_by', 'created_at')
    search_fields = ('name', 'created_by__username')
    list_filter = ('created_at',)

# Personalización del modelo GroupParticipation
class GroupParticipationAdmin(admin.ModelAdmin):
    list_display = ('user', 'group', 'amount_contributed')
    search_fields = ('user__username', 'group__name')
    list_filter = ('group',)



@admin.register(SavingsChallenge)
class SavingsChallengeAdmin(admin.ModelAdmin):
    list_display = ('name', 'goal_amount', 'weeks', 'created_at')
# Registra los modelos
admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(GroupSavings, GroupSavingsAdmin)
admin.site.register(GroupParticipation, GroupParticipationAdmin)



@admin.register(InvestOption)
class InvestOptionAdmin(admin.ModelAdmin):
    list_display = ('name', 'yield_rate', 'minimum_investment', 'created_at')
    search_fields = ('name', 'description')
    list_filter = ('created_at',)