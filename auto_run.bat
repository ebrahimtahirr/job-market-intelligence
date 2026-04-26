@echo off
cd "C:\Users\Ebrahim Tahir\Desktop\VSC\job_pipeline"
call venv\Scripts\activate
python pipeline.py
python enricher.py
git add jobs.db
git commit -m "Auto update jobs.db"
git push
echo Done.