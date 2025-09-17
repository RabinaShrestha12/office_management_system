from django.http import HttpResponse
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from io import BytesIO
from django.conf import settings
import os
from datetime import datetime
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import  AllowAny
from rest_framework.response import Response
from rest_framework import status
from ..models import Certificate
from ..serializers import CertificateSerializer
from reportlab.platypus import Paragraph, Frame
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.enums import TA_JUSTIFY
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, Frame, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

def generate_certificate(request, cert_id):
    try:
        # Get certificate object
        try:
            cert = Certificate.objects.get(id=cert_id)
        except Certificate.DoesNotExist:
            return HttpResponse("Certificate not found", status=404)

        buffer = BytesIO()
        p = canvas.Canvas(buffer, pagesize=A4)
        width, height = A4

        # ---------- BORDER ----------
        margin = 30
        p.setLineWidth(3)
        p.rect(margin, margin, width - 2 * margin, height - 2 * margin)

        # ---------- ADD BACKGROUND LOGO ----------
        logo_path = os.path.join(settings.BASE_DIR, "myapp", "media", "Lunar IT Logo.png")
        if os.path.exists(logo_path):
            logo_width = 300
            logo_height = 300
            p.saveState()
            try:
                p.setFillAlpha(0.15)
            except:
                pass
            p.drawImage(
                logo_path,
                (width - logo_width) / 2,
                (height - logo_height) / 2,
                width=logo_width,
                height=logo_height,
                preserveAspectRatio=True,
                mask='auto'
            )
            p.restoreState()

        # ---------- TITLE ----------
        p.setFont("Helvetica-Bold", 30)
        p.drawCentredString(width / 2, height - 100, "Certificate of Completion")

        # ---------- BODY PARAGRAPH ----------
        body_text = f"""
        <b>This is to certify that {cert.name}</b> has successfully completed the role of 
        <i>{cert.role_field}</i> at <b>{cert.company}</b>.<br/><br/>
        The internship program commenced on <b>{cert.joined_date.strftime('%d %B %Y')}</b> 
        and concluded on <b>{cert.end_date.strftime('%d %B %Y')}</b>, covering a total of 
        <b>{cert.working_days} working days</b>.<br/><br/>
        During this period, <b>{cert.name}</b> demonstrated remarkable commitment, dedication, 
        and professionalism towards all assigned tasks. We proudly recognize their hard work 
        and achievements during the internship program.
        """

        # Style with justification and line spacing
        styles = getSampleStyleSheet()
        style = ParagraphStyle(
            name="CertificateBody",
            parent=styles["Normal"],
            fontSize=14,
            leading=24,  # line spacing
            alignment=TA_JUSTIFY,
        )
        paragraph = Paragraph(body_text, style)

        # Frame inside the border
        frame_x = margin + 15*mm
        frame_y = margin + 100
        frame_width = width - 2*margin - 30*mm
        frame_height = height - 250

        frame = Frame(frame_x, frame_y, frame_width, frame_height, showBoundary=0)
        frame.addFromList([paragraph], p)

        # ---------- SIGNATURE ----------
        sig_width = 180
        sig_height = 60
        sig_y = margin + 40
        sig_x = (width - sig_width) / 2

        p.setLineWidth(1)
        p.line(sig_x, sig_y + sig_height + 25, sig_x + sig_width, sig_y + sig_height + 25)

        p.setFont("Helvetica-Bold", 12)
        p.drawCentredString(sig_x + sig_width / 2, sig_y + sig_height + 10, "Supervisor Signature")

        if cert.supervisor_signature:
            signature_path = os.path.join(settings.MEDIA_ROOT, str(cert.supervisor_signature))
            if os.path.exists(signature_path):
                p.drawImage(signature_path, sig_x, sig_y, width=sig_width, height=sig_height,
                            preserveAspectRatio=True, mask='auto')

        # ---------- SAVE PDF ----------
        p.showPage()
        p.save()
        buffer.seek(0)

        response = HttpResponse(buffer, content_type="application/pdf")
        response['Content-Disposition'] = f'attachment; filename="certificate_{cert_id}.pdf"'
        return response

    except Exception as e:
        return HttpResponse(f"Error generating certificate: {str(e)}", status=500)

# ---------------- CREATE / GET ALL ----------------
@api_view(['GET', 'POST'])
@permission_classes([AllowAny])
def certificates(request):
    if request.method == 'GET':
        try:
            if request.user.role == 'admin':
                certificates = Certificate.objects.all().order_by('-joined_date')
            else:
                certificates = Certificate.objects.filter(name=request.user.get_full_name())

            serializer = CertificateSerializer(certificates, many=True)
            return Response({'certificates': serializer.data, 'count': certificates.count()},
                            status=status.HTTP_200_OK)

        except Exception as e:
            return Response({'error': "Failed to fetch certificates", 'details': str(e)},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    elif request.method == 'POST':
        try:
            name = request.data.get('name')
            company = request.data.get('company')
            role_field = request.data.get('role_field')
            joined_date_str = request.data.get('joined_date')
            end_date_str = request.data.get('end_date')
            working_days = request.data.get('working_days')
            supervisor_signature = request.data.get('supervisor_signature')

            if not name or not company or not role_field:
                return Response({'error': "Name, company, and role_field are required"},
                                status=status.HTTP_400_BAD_REQUEST)

            # Validate dates
            try:
                joined_date = datetime.strptime(joined_date_str, "%Y-%m-%d").date()
            except Exception:
                return Response({"error": "Invalid joined_date format. Use YYYY-MM-DD"}, status=400)

            try:
                end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
            except Exception:
                return Response({"error": "Invalid end_date format. Use YYYY-MM-DD"}, status=400)

            # Validate working_days
            try:
                working_days = int(working_days)
                if working_days <= 0:
                    return Response({'error': "working_days must be greater than zero"},
                                    status=status.HTTP_400_BAD_REQUEST)
            except Exception:
                return Response({'error': "Invalid working_days format"}, status=status.HTTP_400_BAD_REQUEST)

            data = {
                "name": name,
                "company": company,
                "role_field": role_field,
                "joined_date": joined_date,
                "end_date": end_date,
                "working_days": working_days,
                "supervisor_signature": supervisor_signature
            }

            serializer = CertificateSerializer(data=data)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            return Response({'error': "Failed to create certificate", 'details': str(e)},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)

