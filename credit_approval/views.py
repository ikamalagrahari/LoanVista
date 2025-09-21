from django.http import HttpResponse


def home(request):
    return HttpResponse("""
    <html>
    <head>
        <title>Credit Approval System</title>
        <style>
            body { font-family: Arial, sans-serif; text-align: center; padding: 50px; }
            h1 { color: #4CAF50; }
        </style>
    </head>
    <body>
        <h1>Backend API is Running!</h1>
        <p>The Credit Approval System API is operational.</p>
        <p>API endpoints are available at <a href="/api/">/api/</a></p>
        <p>Admin interface at <a href="/admin/">/admin/</a></p>
    </body>
    </html>
    """)