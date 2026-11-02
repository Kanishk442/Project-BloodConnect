# BloodConnect 🩸

AI-assisted blood donation platform: donors book appointments and earn badges, hospitals record donations and run image-based screening (WBC cell type, malaria, leukemia, sickle cell) on blood-smear images.

> ⚠️ **Educational/research project. Not a medical device.** Model outputs are screening hints, not diagnoses, and have not been clinically validated. Always consult a qualified doctor.

## Stack
Flask · Flask-JWT-Extended · MySQL (TiDB Cloud in production) · TensorFlow-trained CNN/MobileNetV2 models served via TFLite (LiteRT) · HTML/CSS/JS

## Models
| Model | Reported validation accuracy (training time) |
|---|---|
| WBC classifier | 85% |
| Malaria | 85% |
| Leukemia (ALL) | 87% |
| Sickle cell | 86% |

Models are shipped as `.tflite` in `backend/models/` (~34 MB total, ~130 MB RAM at runtime). Original Keras files are kept in `model_sources/` for retraining/re-export.

## Run locally
```bash
git clone https://github.com/Kanishk442/BloodConnect.git && cd BloodConnect
python -m venv venv && source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env                                   # edit MySQL credentials
python database/init_db.py --demo                      # creates tables + demo logins
cd backend && python app.py                            # http://localhost:5000
```
Demo logins (password `Demo@1234`): `donor@demo.com`, `hospital@demo.com`.

## Deploy (free): TiDB Cloud Starter + Render
1. **Database** – create a free *TiDB Cloud Starter* cluster (MySQL-compatible). Copy host / user / password; port is `4000`.
2. Run the schema once from your machine: set `MYSQL_HOST`, `MYSQL_PORT=4000`, `MYSQL_USER`, `MYSQL_PASSWORD`, `MYSQL_SSL=true` in `.env`, then `python database/init_db.py`.
3. **Hosting** – on Render: *New → Blueprint* → select this repo (uses `render.yaml`). Fill `MYSQL_HOST`, `MYSQL_USER`, `MYSQL_PASSWORD` when prompted.
4. Open the Render URL → `/health` should return `{"status":"healthy"}`.

Free Render services sleep after 15 min idle (first request takes ~1 min). Uploaded images are stored on ephemeral disk.

## Environment variables
See `.env.example`. In production (`APP_ENV=production`) the app refuses to start without `SECRET_KEY` / `JWT_SECRET_KEY`.

## Project layout
```
backend/      Flask app, routes, ML (tflite_model.py, disease_detector.py, ml_integration.py)
frontend/     HTML/CSS/JS pages (served by Flask)
database/     schema.sql, init_db.py
model_sources/ original Keras models
dev_tools/    old training / experiment scripts
```

## Author
Kanishk Tomar · Licensed under the terms in `LICENSE`.
