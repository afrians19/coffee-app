# Coffee Brewing App

A Streamlit app for coffee brewing guidance, dial-in logging, cupping forms, and simple coffee recommendations.

## What This App Does

This project combines four tools in one interface:

1. `Brewing Guide`
   Helps you choose brewing inputs and review previous dial-in results from Google Sheets.
2. `Basic Cupping Form`
   Lets you log everyday dial-in sessions and upload them to a spreadsheet.
3. `SCA Cupping Form`
   Lets you record a more detailed Specialty Coffee Association style evaluation.
4. `Coffee Recommendation`
   Suggests a coffee based on a small taste-preference questionnaire.

The app reads coffee data from Google Sheets and, in some pages, writes new dial-in records back to those sheets.

## Main Screens

### 1. Brewing Guide

Use this page to:

- look up a coffee by `Coffee ID`
- review the coffee's stock data
- get espresso and filter recipe suggestions
- browse previous dial-in records
- filter dial-in history by numeric values and text
- view a tasting wheel based on the coffee notes

Main inputs:

- `Coffee ID`
- `Grind Size (micron)` or grinder reference
- `Dose`
- `Coffee Strength`
- `Taste Profile`

Main outputs:

- coffee information from the stock sheet
- suggested brew temperature
- espresso recipe estimate
- filter recipe estimate
- previous espresso dial-in records
- previous filter dial-in records
- recipe guide ratios
- flavor wheel

Dialed recipe filtering:

- Numeric columns support operators such as `>`, `<`, `>=`, `<=`, `==`, `!=`
- Text columns support partial search
- You can type part of a word, a few letters, or a full word
- Text filtering is case-insensitive

Typical text filter examples:

- `ssp` in `grinder`
- `tur` in `brew_method`
- `flat` in `brew_tool`
- `berry` in `notes`

### 2. Basic Cupping Form

Use this page when you want a fast everyday brew log.

You can:

- enter brew details
- score the cup
- add tasting notes
- preview the coffee stock data
- visualize the coffee notes
- upload the record to the `Dial-in Basic` Google Sheet
- build a small in-session table and download it as CSV

Typical workflow:

1. Enter `Coffee ID` and brew details in the sidebar.
2. Adjust scores such as aroma, acidity, sweetness, flavor, body, aftertaste, and rating.
3. Add notes and recipe notes.
4. Check the coffee data shown in the page.
5. Click `Spreadsheet Upload Basic` to save the record to Google Sheets.
6. Optionally click `Add new value` to collect multiple entries in-session.
7. Click `Download data (.csv)` if you want a local CSV export.

### 3. SCA Cupping Form

Use this page when you want a more detailed cupping record.

You can record:

- brew details
- aroma and fragrance
- dry and break evaluation
- flavor, aftertaste, acidity, body
- balance, uniformity, clean cup, sweetness
- notes and recipe notes

This page also:

- shows coffee stock data
- shows the flavor wheel
- shows a radar chart of sensory scores
- uploads records to the `Dial-in SCA` Google Sheet
- supports in-session CSV download

Typical workflow:

1. Enter the brew and roast details in the sidebar.
2. Fill in sensory scores and descriptive notes.
3. Review the stock and tasting visualizations.
4. Click `Spreadsheet Upload SCA` to save the record.
5. Optionally collect extra rows and export them as CSV.

### 4. Coffee Recommendation

Use this page when you want a simple coffee suggestion.

You only answer two preference questions:

- preferred profile: `Sweet` or `Acidic`
- preferred flavor: `Chocolaty / Caramel`, `Bright / Citrusy`, or `Fruity`

Then click the prediction button to:

- run the saved recommendation model
- get a suggested coffee
- display matching coffees from the stock sheet

## How To Run Locally

### Requirements

- Python 3
- the packages in [`requirements.txt`](/f:/Cloud/GoogleDrive/Data%20Science/Github%20-%20afrians19/Streamlit-%20coffee-app/requirements.txt)
- access to the Google service account credentials used by Streamlit secrets

### Install

```bash
pip install -r requirements.txt
```

### Start the app

```bash
streamlit run app.py
```

Then open the local Streamlit URL shown in your terminal.

## Google Sheets / Secrets Setup

This app uses:

- `gspread`
- `google.oauth2.service_account.Credentials`
- `st.secrets["gcp_service_account"]`

To run the app successfully, your Streamlit secrets must include a valid Google service account with access to the spreadsheet named `Coffee Stock`.

The code currently expects these worksheets to exist:

- `Stock`
- `Dial-in Basic`
- `Dial-in SCA`

If the spreadsheet name, worksheet names, or credentials are wrong, the app will fail when loading or uploading data.

## Navigation

The app uses a multi-page menu from the main screen.

From the home page you can open:

- `Brewing Guide`
- `Basic Cupping Form`
- `SCA Cupping Form`
- `Coffee Recommendation`

## Files That Matter

- [`app.py`](/f:/Cloud/GoogleDrive/Data%20Science/Github%20-%20afrians19/Streamlit-%20coffee-app/app.py)
  Main Streamlit entry point and page registration.
- [`multiapp.py`](/f:/Cloud/GoogleDrive/Data%20Science/Github%20-%20afrians19/Streamlit-%20coffee-app/multiapp.py)
  Multi-page app helper.
- [`apps/recipe.py`](/f:/Cloud/GoogleDrive/Data%20Science/Github%20-%20afrians19/Streamlit-%20coffee-app/apps/recipe.py)
  Brewing Guide page.
- [`apps/basic.py`](/f:/Cloud/GoogleDrive/Data%20Science/Github%20-%20afrians19/Streamlit-%20coffee-app/apps/basic.py)
  Basic dial-in page.
- [`apps/sca_form.py`](/f:/Cloud/GoogleDrive/Data%20Science/Github%20-%20afrians19/Streamlit-%20coffee-app/apps/sca_form.py)
  SCA cupping page.
- [`apps/rec_coffee.py`](/f:/Cloud/GoogleDrive/Data%20Science/Github%20-%20afrians19/Streamlit-%20coffee-app/apps/rec_coffee.py)
  Coffee recommendation page.

## Common Troubleshooting

### `streamlit has no attribute ...`

This project pins an older Streamlit version in `requirements.txt`. If you add newer Streamlit UI APIs, they may fail on the current version.

### Google Sheets connection fails

Check:

- your `secrets.toml`
- service account permissions
- the spreadsheet name
- worksheet names

### Upload button does not work

Check whether:

- the target worksheet exists
- the service account has write access
- the row format still matches the sheet columns

## Current Limitations

- The app depends on a private Google Sheet structure.
- Some labels and UI text are still inconsistent across pages.
- The app is tightly coupled to the current spreadsheet schema.
- Recommendation output depends on the bundled saved model file.

## Quick Start For Daily Use

If you only want to use the app and not modify it:

1. Run `streamlit run app.py`
2. Open `Brewing Guide` to review a coffee and generate brew suggestions
3. Open `Basic Cupping Form` or `SCA Cupping Form` to log a session
4. Upload the record to Google Sheets if needed
5. Use `Coffee Recommendation` when you want a simple coffee suggestion
