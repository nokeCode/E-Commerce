from .forms import AccountForm
from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from django.contrib import messages
from django.contrib.auth.hashers import make_password
from .models import Users
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.shortcuts import redirect
from django.contrib.auth.hashers import make_password
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import Group, User
from django.contrib.auth import logout
from django.core.cache import cache
from django.utils.crypto import get_random_string
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth import login as auth_login
from django.views.decorators.http import require_POST
from django.utils import timezone
from django.core.cache import cache
from django.http import JsonResponse
from django.utils.timezone import now, timedelta
#import xlwt
from django.http import HttpResponseForbidden
from django.template.loader import render_to_string
from django.shortcuts import render, redirect
from django.contrib.auth.forms import PasswordResetForm
from django.contrib.auth.tokens import default_token_generator
#from django.contrib.auth.models import User
from django.contrib.sites.shortcuts import get_current_site
from django.core.mail import send_mail
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str

@login_required
def account(request):
    # Récupérer les favoris de l'utilisateur
    try:
        from products.models import Favorite
        favorites_qs = request.user.favorites.select_related('product').all()
    except Exception:
        favorites_qs = []

    return render(request, 'accounts/account.html', {
        'favorites': favorites_qs,
    })

@login_required
def account_profile(request):
    """Page de profil utilisateur"""
    # Récupérer le profil de l'utilisateur
    try:
        profile = Users.objects.get(user=request.user)
    except Users.DoesNotExist:
        # Créer un profil si inexistant
        user = Users.objects.create(user=request.user)
 
    context = {
        'user': request.user
    }
    return render(request, 'accounts/account.html', context)

# accounts/views.py - Ajoutez cette vue

@login_required

def update_profile(request):
    """Mise à jour des informations personnelles et préférences de communication"""
    user = request.user
    
    try:
        # Mise à jour des informations utilisateur (dans le modèle Users)
        user.first_name = request.POST.get('first_name', '').strip()
        user.last_name = request.POST.get('last_name', '').strip()
        user.phone = request.POST.get('phone', '').strip()
        
        # Date de naissance
        birth_date = request.POST.get('birth_date', '').strip()
        if birth_date:
            print(birth_date)
            user.birth_date = birth_date
        else:
            user.birth_date = None
        
        # Genre
        gender = request.POST.get('gender', '').strip()
        if gender in ['male', 'female', 'other']:
            user.gender = gender
        else:
            user.gender = ''
        
        user.save()
        
        # Mise à jour des préférences de communication (dans CustomerProfile)
        '''user.newsletter = request.POST.get('newsletter') == 'on'
        user.promo_emails = request.POST.get('promotions') == 'on'
        user.sms_notifications = request.POST.get('sms') == 'on'
        user.security_alerts = request.POST.get('security_alerts') == 'on'
        user.save()'''
        
        messages.success(request, f" Votre profil a été mis à jour avec succès. Mais le nom d'utilisateur est {user.username}")
        
    except Exception as e:
        messages.error(request, f" Erreur lors de la mise à jour : {str(e)}")
    
    return redirect('account')


@login_required
def account_orders(request):
    """Retourne le partial HTML des commandes (param ?partial=1 ou requête XHR) ou export CSV/JSON via ?export=csv|json"""
    from orders.models import Order

    qs = Order.objects.filter(user=request.user).select_related('payment').order_by('-created_at')
    export = request.GET.get('export')

    if export in ('csv', 'json'):
        # Export
        if export == 'csv':
            import csv
            from django.http import HttpResponse
            response = HttpResponse(content_type='text/csv')
            response['Content-Disposition'] = f'attachment; filename="orders-{request.user.username}.csv"'
            writer = csv.writer(response)
            writer.writerow(['order_number', 'date', 'total', 'status', 'payment_method', 'payment_status', 'transaction_id'])
            for o in qs:
                pay = getattr(o, 'payment', None)
                writer.writerow([o.order_number, o.created_at.isoformat(), str(o.total), o.status, pay.method if pay else '', pay.status if pay else '', pay.transaction_id if pay else ''])
            return response
        else:
            data = []
            for o in qs:
                pay = getattr(o, 'payment', None)
                data.append({
                    'order_number': o.order_number,
                    'date': o.created_at.isoformat(),
                    'total': str(o.total),
                    'status': o.status,
                    'payment_method': pay.method if pay else None,
                    'payment_status': pay.status if pay else None,
                    'transaction_id': pay.transaction_id if pay else None,
                })
            return JsonResponse(data, safe=False)

    # Partial HTML for AJAX
    if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.GET.get('partial'):
        return render(request, 'accounts/partials/orders_list.html', {'orders': qs})

    # Fallback : rendre la page de compte (avec orders en contexte)
    return render(request, 'accounts/account.html', {'orders': qs})


@login_required
def account_addresses(request):
    """Partial HTML et export pour les adresses : récupère l'adresse profil + adresses de livraison des commandes passées"""
    from orders.models import ShippingAddress
    from .models import CustomerProfile

    addresses = []

    # Adresse du profil si renseignée
    try:
        profile = CustomerProfile.objects.get(user=request.user)
        if profile and profile.address:
            addresses.append({
                'full_name': request.user.get_full_name() or request.user.username,
                'address': profile.address,
                'city': profile.city,
                'postal_code': profile.postal_code,
                'country': profile.country,
                'phone': '',
                'is_default': True
            })
    except CustomerProfile.DoesNotExist:
        profile = None

    # Adresses issues des commandes passées
    sh_qs = ShippingAddress.objects.filter(order__user=request.user).order_by('-order__created_at')
    seen = set()
    for s in sh_qs:
        key = (s.full_name, s.address, s.city, s.postal_code, s.country, s.phone)
        if key in seen:
            continue
        seen.add(key)
        addresses.append({
            'full_name': s.full_name or request.user.get_full_name() or request.user.username,
            'address': s.address,
            'city': s.city,
            'postal_code': s.postal_code,
            'country': s.country,
            'phone': s.phone,
            'is_default': False
        })

    export = request.GET.get('export')
    if export in ('csv', 'json'):
        if export == 'csv':
            import csv
            from django.http import HttpResponse
            response = HttpResponse(content_type='text/csv')
            response['Content-Disposition'] = f'attachment; filename="addresses-{request.user.username}.csv"'
            writer = csv.writer(response)
            writer.writerow(['full_name', 'address', 'postal_code', 'city', 'country', 'phone', 'is_default'])
            for a in addresses:
                writer.writerow([a['full_name'], a['address'], a['postal_code'], a['city'], a['country'], a['phone'], a['is_default']])
            return response
        else:
            return JsonResponse(addresses, safe=False)

    if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.GET.get('partial'):
        return render(request, 'accounts/partials/addresses_list.html', {'addresses': addresses})

    return render(request, 'accounts/account.html', {'addresses': addresses})


@login_required
def account_security(request):
    """Liste des sessions actives de l'utilisateur (partial)."""
    from .models import UserSession
    from django.contrib.sessions.models import Session

    sessions = UserSession.objects.filter(user=request.user)

    # current session key
    current_key = request.session.session_key

    # Partial HTML
    if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.GET.get('partial'):
        return render(request, 'accounts/partials/security_list.html', {
            'sessions': sessions,
            'current_session_key': current_key
        })

    return render(request, 'accounts/account.html', {'sessions': sessions})


@login_required
@require_POST
def account_security_kick(request):
    """Déconnecte une session par session_key (POST)."""
    from .models import UserSession
    from django.contrib.sessions.models import Session

    session_key = request.POST.get('session_key')

    if not session_key:
        return JsonResponse({'success': False, 'error': 'missing_key'}, status=400)

    try:
        us = UserSession.objects.get(session_key=session_key, user=request.user)
    except UserSession.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'not_found'}, status=404)

    # Empêcher la suppression de la session courante depuis cette action
    if request.session.session_key == session_key:
        return JsonResponse({'success': False, 'error': 'cannot_kick_current'}, status=400)

    # Supprimer la session django si existante
    try:
        s = Session.objects.get(session_key=session_key)
        s.delete()
    except Session.DoesNotExist:
        pass

    us.delete()

    return JsonResponse({'success': True})


@login_required
def account_payments(request):
    """Partial HTML et export pour les paiements (CSV/JSON)."""
    from orders.models import Payment

    qs = Payment.objects.filter(order__user=request.user).select_related('order').order_by('-created_at')

    export = request.GET.get('export')
    if export in ('csv', 'json'):
        if export == 'csv':
            import csv
            from django.http import HttpResponse
            response = HttpResponse(content_type='text/csv')
            response['Content-Disposition'] = f'attachment; filename="payments-{request.user.username}.csv"'
            writer = csv.writer(response)
            writer.writerow(['payment_id', 'order_number', 'date', 'amount', 'method', 'provider', 'status', 'transaction_id'])
            for p in qs:
                writer.writerow([p.id, p.order.order_number if p.order else '', p.created_at.isoformat(), str(p.amount), p.method, p.provider, p.status, p.transaction_id or ''])
            return response
        else:
            data = []
            for p in qs:
                data.append({
                    'payment_id': p.id,
                    'order_number': p.order.order_number if p.order else None,
                    'date': p.created_at.isoformat(),
                    'amount': str(p.amount),
                    'method': p.method,
                    'provider': p.provider,
                    'status': p.status,
                    'transaction_id': p.transaction_id,
                    'order_items_count': p.order.items.count() if getattr(p, 'order', None) else 0
                })
            return JsonResponse(data, safe=False)

    if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.GET.get('partial'):
        return render(request, 'accounts/partials/payments_list.html', {'payments': qs})

    return render(request, 'accounts/account.html', {'payments': qs})


@login_required
def account_notifications(request):
    """Partial HTML et export CSV/JSON des notifications de l'utilisateur."""
    from .models import Notification

    qs = Notification.objects.filter(user=request.user).order_by('-created_at')
    export = request.GET.get('export')

    if export in ('csv', 'json'):
        if export == 'csv':
            import csv
            from django.http import HttpResponse
            response = HttpResponse(content_type='text/csv')
            response['Content-Disposition'] = f'attachment; filename="notifications-{request.user.username}.csv"'
            writer = csv.writer(response)
            writer.writerow(['id', 'date', 'title', 'message', 'level', 'is_read'])
            for n in qs:
                writer.writerow([n.id, n.created_at.isoformat(), n.title, n.message, n.level, n.is_read])
            return response
        else:
            data = []
            for n in qs:
                data.append({
                    'id': n.id,
                    'date': n.created_at.isoformat(),
                    'title': n.title,
                    'message': n.message,
                    'level': n.level,
                    'is_read': n.is_read,
                    'link': n.link,
                })
            return JsonResponse(data, safe=False)

    if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.GET.get('partial'):
        return render(request, 'accounts/partials/notifications_list.html', {'notifications': qs})

    return render(request, 'accounts/account.html', {'notifications': qs})


@login_required
@require_POST
def account_notifications_action(request):
    """Actions sur les notifications: mark_read, mark_unread, delete, mark_read_all, delete_read."""
    from .models import Notification

    action = request.POST.get('action')
    nid = request.POST.get('id')  # may be 'all' for bulk ops

    if not action:
        return JsonResponse({'success': False, 'error': 'missing_params'}, status=400)

    if action == 'mark_read_all':
        Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
        return JsonResponse({'success': True})

    if action == 'delete_read':
        Notification.objects.filter(user=request.user, is_read=True).delete()
        return JsonResponse({'success': True})

    if not nid:
        return JsonResponse({'success': False, 'error': 'missing_id'}, status=400)

    try:
        n = Notification.objects.get(id=nid, user=request.user)
    except Notification.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'not_found'}, status=404)

    if action == 'mark_read':
        n.mark_read()
        return JsonResponse({'success': True})
    if action == 'mark_unread':
        n.mark_unread()
        return JsonResponse({'success': True})
    if action == 'delete':
        n.delete()
        return JsonResponse({'success': True})

    return JsonResponse({'success': False, 'error': 'unknown_action'}, status=400)

RESEND_COOLDOWN = 30  # par exemple 30 sec


def signup(request):
    if request.method == 'POST':

        email = request.POST.get('email')
        name = request.POST.get('username')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')

        if not email or not password or not confirm_password:
            messages.error(request, "Tous les champs doivent être remplis.")
            return render(request, "accounts/signup.html")

        if password != confirm_password:
            messages.error(request, "Les mots de passe ne correspondent pas.")
            return render(request, "accounts/signup.html")

        if Users.objects.filter(email=email).exists():
            messages.error(request, "Cet email est déjà utilisé.")
            return render(request, "accounts/signup.html")

        # Découpage du nom
        first_name = last_name = ""
        if name:
            parts = name.strip().split(" ", 1)
            first_name = parts[0]
            if len(parts) > 1:
                last_name = parts[1]

        # Création du compte
        user = Users.objects.create_user(
            username=name,
            email=email,
            first_name=first_name,
            last_name=last_name,
            password=password
        )

        # Connecte l'utilisateur directement
        login(request, user)

        # === 2FA START ===

        now_ts = timezone.now().timestamp()

        # Génération du code
        code_2fa = get_random_string(length=6, allowed_chars='0123456789')

        # Stockage cache (expire en 2 min)
        cache.set(f"2fa_{user.id}", code_2fa, timeout=120)
        cache.set(f"2fa_attempts_{user.id}", 0, timeout=120)

        # Envoi email
        try:
            send_mail(
                subject="Votre code de vérification",
                message=f"Votre code de vérification est : {code_2fa}. Il expire dans 2 minutes.",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=False,
            )
        except Exception as e:
            messages.error(request, "Erreur d’envoi du code : " + str(e))
            return redirect("verify_2fa")

        # Sauvegarde dans la session
        request.session['2fa_user_id'] = user.id
        request.session['2fa_sent_at'] = now_ts

        # Redirection vers la page 2FA
        return redirect("verify_2fa")
        # === 2FA END ===

    return render(request, "accounts/signup.html")

def signin(request):
    if request.method == "POST":

        identifier = request.POST.get("username_or_email")
        password = request.POST.get("password")

        # ✅ PRIORITÉ : GET > POST > session
        next_url = (
            request.GET.get('next')
            or request.POST.get('next')
            or request.session.get('login_next')
            or '/'
        )

        if not identifier or not password:
            messages.error(request, "Veuillez remplir tous les champs.")
            return render(request, "accounts/signin.html", {'next': next_url})

        # email ou username
        if "@" in identifier:
            try:
                user_obj = Users.objects.get(email=identifier)
                username_to_auth = user_obj.username
            except Users.DoesNotExist:
                messages.error(request, "Email ou mot de passe incorrect.")
                return render(request, "accounts/signin.html", {'next': next_url})
        else:
            username_to_auth = identifier

        user = authenticate(request, username=username_to_auth, password=password)

        if user is None:
            messages.error(request, "Identifiants incorrects.")
            return render(request, "accounts/signin.html", {'next': next_url})

        # 🚫 PAS DE login ICI

        # ---------------- 2FA ----------------
        now_ts = timezone.now().timestamp()
        code_2fa = get_random_string(length=6, allowed_chars="0123456789")

        cache.set(f"2fa_{user.id}", code_2fa, timeout=120)

        send_mail(
            subject="Votre code de vérification",
            message=f"Votre code est : {code_2fa}",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
        )

        # ✅ STOCKAGE UNIQUE ET FIABLE
        request.session['2fa_user_id'] = user.id
        request.session['login_next'] = next_url
        request.session['2fa_sent_at'] = now_ts

        return redirect("verify_2fa")

    return render(request, "accounts/signin.html")

def logout_view(request):
    logout(request)
    messages.success(request, 'Vous avez été déconnecté avec succès.')
    return redirect('signin')

MAX_ATTEMPTS = 3
RESEND_COOLDOWN = 60  # secondes

def verify_2fa(request):
    user_id = request.session.get('2fa_user_id')

    # 🔒 Sécurité : accès interdit sans étape login
    if not user_id:
        return redirect('signin')

    tentatives = request.session.get('tentatives_2fa', 0)
    max_attempts = MAX_ATTEMPTS

    if request.method == 'POST':
        code_saisi = request.POST.get('code')
        code_stocke = cache.get(f"2fa_{user_id}")

        # ⛔ Trop de tentatives
        if tentatives >= max_attempts:
            messages.error(
                request,
                "Vous avez dépassé le nombre de tentatives autorisées."
            )
            return redirect('signin')

        # ✅ Code valide
        if code_stocke and code_saisi == code_stocke:
            try:
                user = Users.objects.get(id=user_id)
            except Users.DoesNotExist:
                messages.error(request, "Utilisateur introuvable.")
                return redirect('signin')

            # 🔐 LOGIN FINAL (SEULEMENT ICI)
            auth_login(
                request,
                user,
                backend='django.contrib.auth.backends.ModelBackend'
            )

            # 🧹 Nettoyage session & cache
            request.session.pop('2fa_user_id', None)
            request.session.pop('2fa_sent_at', None)
            request.session.pop('tentatives_2fa', None)
            cache.delete(f"2fa_{user_id}")

            # 🎯 REDIRECTION CORRECTE
            next_url = request.session.pop('login_next', None)

            # Sécurité anti open-redirect
            if not next_url or not next_url.startswith('/'):
                next_url = '/'

            return redirect(next_url)

        # ❌ Code invalide
        tentatives += 1
        request.session['tentatives_2fa'] = tentatives

        if tentatives >= max_attempts:
            messages.error(
                request,
                "Trop de tentatives. Veuillez réessayer plus tard."
            )
            return redirect('signin')

        messages.error(request, "Code invalide. Veuillez réessayer.")

    # ----------- AFFICHAGE PAGE -----------
    try:
        user = Users.objects.get(id=user_id)
        email_masked = mask_email(user.email)
    except Users.DoesNotExist:
        email_masked = None

    last_sent_ts = request.session.get('2fa_sent_at', 0)
    cooldown = 0

    if last_sent_ts:
        elapsed = timezone.now().timestamp() - last_sent_ts
        cooldown = max(0, int(RESEND_COOLDOWN - elapsed))

    return render(request, 'accounts/verify_2fa.html', {
        'attempts_used': tentatives,
        'max_attempts': max_attempts,
        'resend_cooldown': cooldown,
        'user_email_masked': email_masked,
    })
    
    
def mask_email(email):
    # example: a******@gmail.com
    try:
        local, domain = email.split('@', 1)
        if len(local) <= 2:
            masked_local = local[0] + '*'
        else:
            masked_local = local[0] + '*'*(len(local)-2) + local[-1]
        return f"{masked_local}@{domain}"
    except:
        return email

@require_POST
def resend_2fa(request):
    """Ré-envoie le code 2FA si RESEND_COOLDOWN s'est écoulé."""
    user_id = request.session.get('2fa_user_id')
    if not user_id:
        return JsonResponse({'success': False, 'error': 'Session 2FA introuvable'}, status=400)

    last_sent = request.session.get('2fa_sent_at', 0)
    now_ts = timezone.now().timestamp()
    elapsed = now_ts - last_sent if last_sent else RESEND_COOLDOWN + 1

    if elapsed < RESEND_COOLDOWN:
        return JsonResponse({'success': False, 'cooldown': int(RESEND_COOLDOWN - elapsed)}, status=429)

    code = get_random_string(length=6, allowed_chars='0123456789')
    cache.set(f"2fa_{user_id}", code, timeout=120)

    try:
        user = Users.objects.get(pk=user_id)
    except Users.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Utilisateur introuvable'}, status=404)

    try:
        send_mail(
            subject="Votre code de vérification",
            message=f"Votre code est : {code}. Il expire dans 2 minutes.",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False,
        )
    except Exception as e:
        error_message = str(e)
        if "Maximum credits exceeded" in error_message or "401" in error_message:
            # quota atteint — informer côté client (front) et autoriser la page verify_2fa
            request.session['2fa_sent_at'] = now_ts
            return JsonResponse({'success': True, 'warning': 'quota_exceeded', 'cooldown': RESEND_COOLDOWN})
        return JsonResponse({'success': False, 'error': f"Erreur envoi mail: {error_message}"}, status=500)

    request.session['2fa_sent_at'] = now_ts
    return JsonResponse({'success': True, 'cooldown': RESEND_COOLDOWN})

def twofa_status(request):
    """Retourne l'état actuel (tentatives, cooldown restant, bloqué) en JSON."""
    user_id = request.session.get('2fa_user_id')
    if not user_id:
        return JsonResponse({'success': False, 'error': 'Session 2FA introuvable'}, status=400)

    tentatives = request.session.get('tentatives_2fa', 0)
    max_attempts = MAX_ATTEMPTS
    last_sent = request.session.get('2fa_sent_at', 0)
    cooldown = 0
    if last_sent:
        elapsed = timezone.now().timestamp() - last_sent
        cooldown = max(0, int(RESEND_COOLDOWN - elapsed))

    blocked = tentatives >= MAX_ATTEMPTS
    return JsonResponse({
        'success': True,
        'attempts_used': tentatives,
        'max_attempts': max_attempts,
        'cooldown': cooldown,
        'blocked': blocked
    })

def password_reset_request(request):
    if request.method == "POST":
        form = PasswordResetForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            associated_users = Users.objects.filter(email=email)
            if associated_users.exists():
                for user in associated_users:
                    # Préparer l'email
                    subject = "Réinitialisation de mot de passe"
                    # Utiliser l'hôte de la requête pour générer le lien (évite d'utiliser
                    # la table `django_site` si elle contient un domaine erroné comme example.com)
                    domain = request.get_host()
                    email_template_name = "accounts/password_reset_email.html"
                    context = {
                        'email': user.email,
                        'domain': domain,
                        'site_name': getattr(settings, 'SITE_NAME', domain),
                        'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                        'user': user,
                        'token': default_token_generator.make_token(user),
                        'protocol': 'https' if request.is_secure() else 'http',
                    }
                    email_content = render_to_string(email_template_name, context)
                    
                    # Envoyer l'email
                    try:
                        # Envoi du mail avec SendGrid (comme dans user_login)
                        send_mail(
                            subject=subject,
                            message=email_content,
                            from_email=settings.DEFAULT_FROM_EMAIL,
                            recipient_list=[user.email],
                            fail_silently=False,
                        )

                    except Exception as e:
                        error_message = str(e)
                        print(f"[❌] Erreur envoi email reset : {error_message}")

                        # 🔍 Vérifie si c’est un problème de crédit SendGrid ou d’authentification
                        if "Maximum credits exceeded" in error_message or "401" in error_message:
                            print("[⚠️] Crédit SendGrid épuisé — affichage d’un message à l’utilisateur.")
                            messages.warning(
                                request,
                                "Le service d’envoi d’email est temporairement indisponible. "
                                "Veuillez réessayer plus tard ou contacter l’administrateur."
                            )
                            return redirect('password_reset_done')  # on reste sur la page
                        else:
                            print(f"[❌] Erreur inconnue lors de l’envoi de l’email : {error_message}")
                            messages.error(request, "Une erreur est survenue lors de l’envoi de l’email de réinitialisation.")
                            return redirect('password_reset')

                
                return redirect('password_reset_done')
            else:
                messages.error(request, "Aucun compte n'est associé à cet email.")
    
    else:
        form = PasswordResetForm()
    
    return render(request, 'accounts/password_reseet.html', {'form': form})

def password_reset_done(request):
    return render(request, 'accounts/password_reset_done.html')

def password_reset_confirm(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = Users.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, Users.DoesNotExist):
        user = None
    
    if user is not None and default_token_generator.check_token(user, token):
        if request.method == "POST":
            new_password = request.POST.get('new_password')
            confirm_password = request.POST.get('confirm_password')
            
            if new_password == confirm_password:
                user.set_password(new_password)
                user.save()
                messages.success(request, "Votre mot de passe a été réinitialisé avec succès.")
                return redirect('password_reset_complete')
            else:
                messages.error(request, "Les mots de passe ne correspondent pas.")
        
        return render(request, 'accounts/password_reset_confirm.html')
    else:
        messages.error(request, "Le lien de réinitialisation est invalide ou a expiré.")
        return redirect('password_reset')

def password_reset_complete(request):
    return render(request, 'accounts/password_reset_complete.html')


