from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import HttpResponse
from .forms import ClientForm, QuoteForm, CarForm
from .models import Client, Quote, Car
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch
from reportlab.platypus import Table, TableStyle, Paragraph
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from django.db.models import Q
import io
import logging

# Set up logging
logger = logging.getLogger(__name__)


def add_quote(request):
    if request.method == 'POST':
        client_form = ClientForm(request.POST)
        quote_form = QuoteForm(request.POST)
        car_form = CarForm(request.POST)

        selected_client = quote_form.data.get('client')
        if selected_client and selected_client != '':
            if quote_form.is_valid() and (car_form.is_valid() or not car_form['car_reg'].value()):
                quote = quote_form.save(commit=False)
                quote.client_id = selected_client
                quote.save()
                if car_form.is_valid() and car_form.cleaned_data['car_reg']:
                    car, _ = Car.objects.get_or_create(
                        client_id=selected_client, car_reg=car_form.cleaned_data['car_reg'])
                    quote.car = car
                    quote.save()
                messages.success(
                    request, f"Quote for {quote.service} created successfully for {quote.client.name}!")
                return redirect('add_quote')
            else:
                messages.error(
                    request, "Please fill in all required quote fields (service and price) and a valid car registration if provided.")
                return render(request, 'quotes/add_quote.html', {
                    'client_form': client_form,
                    'quote_form': quote_form,
                    'car_form': car_form
                })

        has_client_data = any(request.POST.get(field)
                              for field in ['name', 'email', 'phone'])
        if has_client_data:
            if client_form.is_valid():
                new_client = client_form.save()
                if quote_form.is_valid() and (car_form.is_valid() or not car_form['car_reg'].value()):
                    quote = quote_form.save(commit=False)
                    quote.client = new_client
                    quote.save()
                    if car_form.is_valid() and car_form.cleaned_data['car_reg']:
                        car, _ = Car.objects.get_or_create(
                            client=new_client, car_reg=car_form.cleaned_data['car_reg'])
                        quote.car = car
                        quote.save()
                    messages.success(
                        request, f"Quote for {quote.service} created successfully for {new_client.name}!")
                    return redirect('add_quote')
                else:
                    messages.error(
                        request, "Please fill in all required quote fields (service and price) and a valid car registration if provided.")
            else:
                messages.error(
                    request, "Please provide a valid name for the new client.")
        else:
            messages.error(
                request, "Please either add a new client (at least a name) or select an existing client.")

        return render(request, 'quotes/add_quote.html', {
            'client_form': client_form,
            'quote_form': quote_form,
            'car_form': car_form
        })

    else:
        client_form = ClientForm()
        quote_form = QuoteForm()
        car_form = CarForm()

    return render(request, 'quotes/add_quote.html', {
        'client_form': client_form,
        'quote_form': quote_form,
        'car_form': car_form
    })


def client_list(request):
    clients = Client.objects.all().order_by('-created_at')
    search_query = request.GET.get('search', '').lower()

    if search_query:
        clients = clients.filter(
            Q(name__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(phone__icontains=search_query) |
            Q(cars__car_reg__icontains=search_query)
        ).distinct()

    return render(request, 'quotes/client_list.html', {
        'clients': clients,
        'search_query': search_query
    })


def client_detail(request, client_id):
    client = get_object_or_404(Client, id=client_id)
    quotes = Quote.objects.filter(client=client).order_by('-created_at')
    return render(request, 'quotes/client_detail.html', {
        'client': client,
        'quotes': quotes
    })


def edit_client(request, client_id):
    client = get_object_or_404(Client, id=client_id)
    if request.method == 'POST':
        client_form = ClientForm(request.POST, instance=client)
        car_form = CarForm(request.POST)
        logger.info(f"POST data received: {request.POST}")
        logger.info(f"Before save - Client data: {client.__dict__}")
        if client_form.is_valid() and (car_form.is_valid() or not car_form['car_reg'].value()):
            try:
                client = client_form.save()
                if car_form.is_valid() and car_form.cleaned_data['car_reg']:
                    Car.objects.get_or_create(
                        client=client, car_reg=car_form.cleaned_data['car_reg'])
                client.refresh_from_db()
                logger.info(f"After save - Client data: {client.__dict__}")
                messages.success(
                    request, f"Client {client.name} updated successfully!")
                return redirect('client_list')
            except Exception as e:
                logger.error(f"Save failed: {str(e)}")
                messages.error(
                    request, f"Failed to save due to an error: {str(e)}")
                return render(request, 'quotes/edit_client.html', {
                    'client_form': client_form,
                    'car_form': car_form,
                    'client': client
                })
        else:
            logger.info(
                f"Form errors: {client_form.errors} or {car_form.errors}")
            messages.error(
                request, "Failed to save changes. Check the form for errors.")
            messages.error(
                request, f"Form errors: {client_form.errors} or {car_form.errors}")
            return render(request, 'quotes/edit_client.html', {
                'client_form': client_form,
                'car_form': car_form,
                'client': client
            })
    else:
        client_form = ClientForm(instance=client)
        car_form = CarForm()
        logger.info(f"Initial form data: {client_form.initial}")
    return render(request, 'quotes/edit_client.html', {
        'client_form': client_form,
        'car_form': car_form,
        'client': client
    })


def edit_quote(request, quote_id):
    quote = get_object_or_404(Quote, id=quote_id)
    if request.method == 'POST':
        form = QuoteForm(request.POST, instance=quote)
        car_form = CarForm(request.POST)
        if form.is_valid() and (car_form.is_valid() or not car_form['car_reg'].value()):
            try:
                quote = form.save()
                if car_form.is_valid() and car_form.cleaned_data['car_reg']:
                    car, _ = Car.objects.get_or_create(
                        client=quote.client, car_reg=car_form.cleaned_data['car_reg'])
                    quote.car = car
                    quote.save()
                messages.success(
                    request, f"Quote for {quote.service} updated successfully!")
                return redirect('client_detail', quote.client.id)
            except Exception as e:
                logger.error(f"Save failed: {str(e)}")
                messages.error(
                    request, f"Failed to save due to an error: {str(e)}")
                return render(request, 'quotes/edit_quote.html', {
                    'form': form,
                    'car_form': car_form,
                    'quote': quote
                })
        else:
            messages.error(
                request, "Failed to save changes. Check the form for errors.")
            messages.error(
                request, f"Form errors: {form.errors} or {car_form.errors}")
            return render(request, 'quotes/edit_quote.html', {
                'form': form,
                'car_form': car_form,
                'quote': quote
            })
    else:
        form = QuoteForm(instance=quote)
        car_form = CarForm()
    return render(request, 'quotes/edit_quote.html', {
        'form': form,
        'car_form': car_form,
        'quote': quote
    })


def quote_history(request):
    clients = Client.objects.all()
    selected_client = None
    quotes = []
    search_query = request.POST.get('search', '').lower()

    if request.method == 'POST':
        client_id = request.POST.get('client')
        if client_id:
            selected_client = Client.objects.get(id=client_id)
            quotes = Quote.objects.filter(client=selected_client)
        if search_query:
            quotes = Quote.objects.filter(
                client__name__icontains=search_query
            ) | Quote.objects.filter(
                service__icontains=search_query
            )
            if client_id:
                quotes = quotes.filter(client=selected_client)

    return render(request, 'quotes/quote_history.html', {
        'clients': clients,
        'selected_client': selected_client,
        'quotes': quotes,
        'search_query': search_query
    })


def generate_quote_pdf(request, quote_id):
    quote = Quote.objects.get(id=quote_id)
    client = quote.client

    buffer = io.BytesIO()
    custom_width, custom_height = 8.27 * inch, 9 * inch
    p = canvas.Canvas(buffer, pagesize=(custom_width, custom_height))
    width, height = custom_width, custom_height

    p.setLineWidth(0.5)
    p.setStrokeColor(colors.black)
    margin = 0.5 * inch
    p.rect(margin, margin, width - 2 * margin,
           height - 2 * margin, stroke=1, fill=0)

    logo_x_position = width - margin - 2 * inch - 0.25 * inch
    logo_y_position = height - margin - 1.2 * inch
    p.drawImage("quotes/static/images/logo.png", logo_x_position,
                logo_y_position, width=2*inch, height=1*inch)

    p.setFont("Helvetica-Bold", 16)
    p.drawString(inch, height - 2.5 * inch, "Xpert Auto Upholstery - Quote")

    p.setFont("Helvetica", 12)
    y_position = height - 3.5 * inch
    p.drawString(inch, y_position, f"Client: {client.name}")
    y_position -= 0.25 * inch
    if client.email:
        p.drawString(inch, y_position, f"Email: {client.email}")
        y_position -= 0.25 * inch
    if client.phone:
        p.drawString(inch, y_position, f"Phone: {client.phone}")
        y_position -= 0.25 * inch
    if quote.car:
        p.drawString(inch, y_position,
                     f"Car Registration: {quote.car.car_reg}")
        y_position -= 0.25 * inch

    styles = getSampleStyleSheet()
    normal_style = styles['Normal']
    service_paragraph = Paragraph(quote.service, normal_style)

    data = [
        ["Service", "Price (R)", "Date"],
        [
            service_paragraph,
            f"R{quote.price}",
            quote.created_at.strftime("%B %d, %Y, %I:%M %p")
        ],
    ]
    table = Table(data, colWidths=[3.5*inch, 1*inch, 2*inch])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('BOX', (0, 0), (-1, -1), 1, colors.black),
        ('GRID', (0, 0), (-1, -1), 0, colors.black),
    ]))

    table_width, table_height = table.wrap(width - 2 * inch, height)
    min_gap = 1 * inch
    table_y_position = y_position - min_gap
    table.drawOn(p, inch, table_y_position)

    p.setFont("Helvetica-Oblique", 10)
    p.drawString(inch, inch, "Thank you for choosing Xpert Auto Upholstery!")

    p.showPage()
    p.save()

    buffer.seek(0)
    pdf = buffer.getvalue()
    buffer.close()

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="quote_{quote_id}.pdf"'
    response.write(pdf)
    return response
