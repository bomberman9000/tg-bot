from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from datetime import datetime
import io

def generate_ttn(cargo, owner, carrier) -> bytes:
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    
    # Заголовок
    c.setFont("Helvetica-Bold", 16)
    c.drawCentredString(width/2, height - 50, "ТРАНСПОРТНАЯ НАКЛАДНАЯ")
    
    c.setFont("Helvetica", 10)
    c.drawString(50, height - 80, f"No {cargo.id} от {datetime.now().strftime('%d.%m.%Y')}")
    
    # Грузоотправитель
    c.setFont("Helvetica-Bold", 11)
    c.drawString(50, height - 120, "1. Грузоотправитель:")
    c.setFont("Helvetica", 10)
    c.drawString(70, height - 140, f"{owner.full_name}")
    c.drawString(70, height - 155, f"ID: {owner.id}")
    
    # Грузополучатель
    c.setFont("Helvetica-Bold", 11)
    c.drawString(50, height - 190, "2. Грузополучатель:")
    c.setFont("Helvetica", 10)
    c.drawString(70, height - 210, f"Указать при получении")
    
    # Перевозчик
    c.setFont("Helvetica-Bold", 11)
    c.drawString(50, height - 250, "3. Перевозчик:")
    c.setFont("Helvetica", 10)
    if carrier:
        c.drawString(70, height - 270, f"{carrier.full_name}")
        c.drawString(70, height - 285, f"ID: {carrier.id}")
    else:
        c.drawString(70, height - 270, "Не назначен")
    
    # Маршрут
    c.setFont("Helvetica-Bold", 11)
    c.drawString(50, height - 320, "4. Маршрут:")
    c.setFont("Helvetica", 10)
    c.drawString(70, height - 340, f"Откуда: {cargo.from_city}")
    c.drawString(70, height - 355, f"Куда: {cargo.to_city}")
    
    # Груз
    c.setFont("Helvetica-Bold", 11)
    c.drawString(50, height - 390, "5. Груз:")
    c.setFont("Helvetica", 10)
    c.drawString(70, height - 410, f"Наименование: {cargo.cargo_type}")
    c.drawString(70, height - 425, f"Вес: {cargo.weight} т")
    c.drawString(70, height - 440, f"Дата загрузки: {cargo.load_date.strftime('%d.%m.%Y')}")
    
    # Стоимость
    c.setFont("Helvetica-Bold", 11)
    c.drawString(50, height - 480, "6. Стоимость перевозки:")
    c.setFont("Helvetica", 10)
    c.drawString(70, height - 500, f"{cargo.price} руб.")
    
    # Подписи
    c.setFont("Helvetica", 9)
    c.drawString(50, 150, "Грузоотправитель ________________")
    c.drawString(300, 150, "Перевозчик ________________")
    c.drawString(50, 100, "Дата ________________")
    c.drawString(300, 100, "Дата ________________")
    
    c.save()
    buffer.seek(0)
    return buffer.getvalue()
