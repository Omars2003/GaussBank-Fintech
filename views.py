from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import get_user_model, login, authenticate
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm  # Usar UserCreationForm de Django
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.shortcuts import resolve_url
from django.contrib import messages
from .models import GroupSavings, GroupParticipation, SavingsChallenge, ChallengeParticipation, WeeklyContribution, BankAccount, InvestOption
from .forms import GroupSavingsForm, ContributionForm, CustomUserCreationForm, EmailAuthenticationForm
from django.db.models.signals import post_save
from django.dispatch import receiver
from decimal import Decimal
import stripe
from django.http import JsonResponse
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt


User = get_user_model()  # Obtiene el modelo de usuario configurado (CustomUser)

def signup(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            form.save()  # Crea el usuario
            return redirect('login')  # Redirige al login después del registro
    else:
        form = CustomUserCreationForm()
    return render(request, 'signup.html', {'form': form})
    


class CustomLoginView(LoginView):
    template_name = 'registration/login.html'  # Ruta de tu plantilla de login
    authentication_form = EmailAuthenticationForm 
    def get_success_url(self):
        return resolve_url('/') 

@login_required  # Asegura que solo los usuarios logueados puedan acceder
def profile(request):
    try:
        # Obtener la cuenta bancaria del usuario actual
        account = BankAccount.objects.get(user=request.user)
    except BankAccount.DoesNotExist:
        # Si no existe, crea una nueva cuenta para el usuario
        account = BankAccount.objects.create(user=request.user)

    # Pasar los datos al contexto
    context = {
        'user': request.user,
        'balance': account.balance,
        'total_deposits': account.total_deposits,
        'active_loans': account.active_loans,
    }
    return render(request, 'accounts/profile.html', context)


def home(request):
    return render(request, 'home.html')
######################################################################################################################################################


@login_required
def group_savings_list(request):
    groups = GroupSavings.objects.all()
    return render(request, 'group_savings_list.html', {'groups': groups})

@login_required
def group_savings_create(request):
    if request.method == 'POST':
        form = GroupSavingsForm(request.POST)
        if form.is_valid():
            group = form.save(commit=False)
            group.created_by = request.user
            group.save()
            GroupParticipation.objects.create(user=request.user, group=group)  # Creador automáticamente participa
            return redirect('group_savings_list')
    else:
        form = GroupSavingsForm()
    return render(request, 'group_savings_create.html', {'form': form})

@login_required
def group_savings_detail(request, group_id):
    group = get_object_or_404(GroupSavings, id=group_id)
    participants = GroupParticipation.objects.filter(group=group)

    if request.method == 'POST':
        form = ContributionForm(request.POST)
        if form.is_valid():
            amount = form.cleaned_data['amount']
            try:
                participation = GroupParticipation.objects.get(user=request.user, group=group)
                participation.contribute(amount)
                messages.success(request, f"Successfully contributed ${amount} to {group.name}.")
            except ValidationError as e:
                messages.error(request, str(e))
            return redirect('group_savings_detail', group_id=group.id)
    else:
        form = ContributionForm()

    return render(request, 'group_savings_detail.html', {'group': group, 'participants': participants, 'form': form})
############################################################################################################################################
@login_required
def savings_challenge(request):
    challenge = SavingsChallenge.objects.first()
    if not challenge:
        messages.error(request, "The 40-Week Savings Challenge is not available. Please contact support.")
        return redirect('home')

    # Obtén o crea la participación del usuario
    participation, created = ChallengeParticipation.objects.get_or_create(user=request.user, challenge=challenge)

    if created or participation.custom_goal_amount == 2000.00:
        if request.method == 'POST':
            custom_goal = request.POST.get('custom_goal')
            if custom_goal:
                participation.custom_goal_amount = float(custom_goal)
                participation.save()
                messages.success(request, f"Your goal of ${custom_goal} has been set.")
                return redirect('savings_challenge')
        return render(request, 'set_goal.html', {'challenge': challenge})

    contributions = WeeklyContribution.objects.filter(participation=participation).order_by('week_number')
    total_contributed = sum(c.contributed_amount for c in contributions)
    weekly_amount = participation.weekly_amount()

    # Genera una lista de semanas (del 1 al número total de semanas del reto)
    weeks_range = list(range(1, challenge.weeks + 1))

    if request.method == 'POST':
        amount = request.POST.get('amount')
        if amount:
            amount = Decimal(amount)
            if request.user.bankaccount.balance >= amount:
                week_number = len(contributions) + 1
                if week_number <= challenge.weeks:
                    WeeklyContribution.objects.create(participation=participation, week_number=week_number, contributed_amount=amount)
                    participation.total_contributed += amount
                    participation.save()
                    request.user.bankaccount.balance -= amount
                    request.user.bankaccount.save()
                    messages.success(request, f"Successfully contributed ${amount} to week {week_number}.")
                else:
                    messages.error(request, "You have completed all weeks of the challenge!")
            else:
                messages.error(request, "Insufficient balance. Please add funds.")
        return redirect('savings_challenge')

    return render(request, 'savings_challenge.html', {
        'challenge': challenge,
        'participation': participation,
        'contributions': contributions,
        'total_contributed': total_contributed,
        'weekly_amount': weekly_amount,
        'weeks_range': weeks_range,  # Pasa la lista a la plantilla
    })


def invest(request):
    invest_options = InvestOption.objects.all()
    return render(request, 'invest.html', {'invest_options': invest_options})

    ############################################################## STRIPE INTEGRATION

stripe.api_key = settings.STRIPE_SECRET_KEY 

stripe.api_key = settings.STRIPE_SECRET_KEY

@csrf_exempt
def create_payment_intent(request):
    if request.method == "POST":
        try:
            # Obtener datos del cliente
            user = request.user
            amount = Decimal(request.POST.get("amount"))  # En dólares, por ejemplo

            # Crear PaymentIntent
            intent = stripe.PaymentIntent.create(
                amount=amount * 100,  # Stripe trabaja en centavos
                currency="usd",  # Cambia la moneda si es necesario
                payment_method_types=["card"],
            )

            # Devolver el client_secret al cliente
            return JsonResponse({"clientSecret": intent["client_secret"]})
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=403)



@csrf_exempt
def payment_successful(request):
    if request.method == "POST":
        try:
            print("Vista `payment_successful` llamada")  # Depuración
            amount = Decimal(request.POST.get("amount"))
            user = request.user

            # Verifica si el usuario está autenticado
            if not user.is_authenticated:
                return JsonResponse({"error": "Usuario no autenticado."}, status=403)

            # Obtener o crear la cuenta bancaria del usuario
            account, created = BankAccount.objects.get_or_create(user=user)

            print(f"Antes de actualizar - Balance: {account.balance}, Total Deposits: {account.total_deposits}")  # Depuración

            # Actualizar balance y total_deposits
            account.balance += amount
            account.total_deposits += amount
            account.save()

            print(f"Después de actualizar - Balance: {account.balance}, Total Deposits: {account.total_deposits}")  # Depuración

            return JsonResponse({"message": "Fondos agregados con éxito."})
        except Exception as e:
            print(f"Error: {e}")  # Depuración
            return JsonResponse({"error": str(e)}, status=500)

@login_required
def deposit_funds_page(request):
    return render(request, 'deposit_funds.html', {
        'stripe_public_key': settings.STRIPE_PUBLIC_KEY
    })


@login_required
def create_checkout_session(request):
    if request.method == "POST":
        try:
            amount = int(request.POST.get("amount")) * 100  # Convertir a centavos
            print(f"Monto recibido: {amount}")  # Depuración

            # Crear la sesión de Stripe Checkout
            session = stripe.checkout.Session.create(
                payment_method_types=["card"],
                line_items=[
                    {
                        "price_data": {
                            "currency": "usd",
                            "product_data": {
                                "name": "Depósito de fondos",
                            },
                            "unit_amount": amount,
                        },
                        "quantity": 1,
                    }
                ],
                mode="payment",
                success_url=f"{request.build_absolute_uri('/add-funds/success/')}",
                cancel_url=f"{request.build_absolute_uri('/profile/')}",
                customer_email=request.user.email,
            )

            print(f"Sesión creada: {session.id}")  # Depuración
            return JsonResponse({"id": session.id})
        except Exception as e:
            print(f"Error al crear la sesión de Stripe: {e}")  # Depuración
            return JsonResponse({"error": f"Error al crear la sesión de Stripe: {e}"}, status=500)
@login_required
def success_view(request):
    session_id = request.GET.get("session_id")  # Captura el session_id de la URL
    if not session_id:
        return render(request, "error.html", {"message": "No se pudo verificar la transacción."})

    try:
        # Consulta la sesión de Stripe usando el session_id
        session = stripe.checkout.Session.retrieve(session_id, api_key=settings.STRIPE_SECRET_KEY)

        # Verifica que el pago fue exitoso
        if session.payment_status == "paid":
            # Obtén el monto pagado
            amount_total = Decimal(session.amount_total / 100)

            # Actualiza la cuenta bancaria del usuario
            account, created = BankAccount.objects.get_or_create(user=request.user)
            account.balance += amount_total
            account.total_deposits += amount_total
            account.save()

            return render(request, "success.html", {"message": "Fondos agregados con éxito."})

    except stripe.error.StripeError as e:
        return render(request, "error.html", {"message": f"Error con Stripe: {e}"})

    return render(request, "error.html", {"message": "No se pudo verificar la transacción."})