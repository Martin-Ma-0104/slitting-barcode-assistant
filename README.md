# Slitting Barcode Assistant

Small internal Streamlit V1 app for generating deterministic slitting barcode data and exporting the MES upload Excel file.

## Install

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Run

```bash
streamlit run app.py
```

## Workflow

1. Enter product width in millimeters, shipment quantity, target yield, and planned small rolls per cut.
2. Calculate the production plan.
3. Select slitters FX1-FX7.
4. Review or manually adjust Master Roll allocation.
5. Paste Master Roll SNs, one per line, and click Apply Master Rolls.
6. Enter slitting date, team, and starting sequence.
7. Review actual small roll quantities per Master Roll.
8. Click Generate, review validation and the eight-column Chinese preview, and download the MES Excel file.

Downloaded Excel files are generated in the browser through Streamlit's download button. They are not automatically uploaded to MES.

## Core Business Rules

- `logic/production.py`: shipment, yield, production quantity, required Master Roll calculations.
- `logic/allocation.py`: automatic and manual slitter allocation validation.
- `logic/validation.py`: Master Roll parsing and final generated data validation.
- `logic/barcode.py`: SR barcode, date code, machine/team code, and LOT ID generation.
- `logic/batch.py`: full deterministic small roll row generation.
- `logic/export_excel.py`: MES Excel format and text-cell preservation.

The app never guesses quantities, serial numbers, machine assignments, or barcode values. Invalid input blocks generation and export.

## Test

```bash
python -m unittest discover -s tests
```

## Fixed Cloud URL

Public application: https://slitting-barcode.streamlit.app/

Source repository: https://github.com/Martin-Ma-0104/slitting-barcode-assistant

Hosted on Streamlit Community Cloud using Python 3.10 and the `main` branch.
Application and source visibility are public, as requested by the owner.
Updates to the hosted app must be committed to this repository; editing the local
workspace alone does not update the cloud app.

1. Keep application source in the repository above. Exclude local environments,
   generated output, and secrets using `.gitignore`.
2. Sign in at https://share.streamlit.io/ and connect that repository.
3. Create an app using the repository's branch and `app.py` as the entrypoint.
   Choose Python 3.10 to match the locally tested runtime.
4. Choose an available app subdomain and deploy. The platform assigns an HTTPS
   address under `streamlit.app`; record the actual address after deployment.
5. Set the app visibility to public, as requested, and verify the URL while signed out.
6. Verify production planning, Apply Master Rolls, Generate, and the downloaded
   Excel's eight Chinese headers before sharing the URL.

The host installs `requirements.txt`. No MES credentials or other application
secrets are required. The app stores inputs and generated results in session state;
it does not keep a durable production history.

The cloud app does not depend on the operator's computer being on. Community Cloud
apps currently sleep after 12 hours without traffic and can be woken by visitors.
A fixed URL does not guarantee uninterrupted availability.

Official setup: https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/deploy
