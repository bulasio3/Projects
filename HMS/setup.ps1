# Create all folders
New-Item -ItemType Directory -Force -Path hospital, core, core\migrations, templates, templates\auth, templates\partials, templates\dashboards, templates\patients, templates\appointments, templates\invoices, static, static\css, static\js, media | Out-Null

# Create empty placeholder files
New-Item -ItemType File -Force -Path hospital\__init__.py, hospital\settings.py, hospital\urls.py, hospital\wsgi.py, hospital\asgi.py | Out-Null
New-Item -ItemType File -Force -Path core\__init__.py, core\apps.py, core\models.py, core\forms.py, core\admin.py, core\views.py, core\urls.py, core\context_processors.py, core\middleware.py, core\tests.py, core\migrations\__init__.py | Out-Null
New-Item -ItemType File -Force -Path templates\base.html, templates\auth\login.html, templates\partials\sidebar.html, templates\partials\topbar.html, templates\partials\stat_card.html, templates\partials\pill.html, templates\partials\call_modal.html | Out-Null
New-Item -ItemType File -Force -Path templates\dashboards\admin.html, templates\dashboards\doctor.html, templates\dashboards\reception.html, templates\dashboards\nurse.html, templates\dashboards\pharmacy.html, templates\dashboards\lab.html, templates\dashboards\patient.html, templates\dashboards\call_center.html | Out-Null
New-Item -ItemType File -Force -Path templates\patients\list.html, templates\patients\form.html, templates\patients\detail.html | Out-Null
New-Item -ItemType File -Force -Path templates\appointments\list.html, templates\appointments\form.html | Out-Null
New-Item -ItemType File -Force -Path templates\invoices\list.html | Out-Null
New-Item -ItemType File -Force -Path static\css\hms.css, static\js\hms.js | Out-Null
New-Item -ItemType File -Force -Path .gitignore, .env.example, requirements.txt, Procfile, runtime.txt, manage.py, README.md | Out-Null

Write-Host "Folders and empty files created successfully!" -ForegroundColor Green