
import os
from data.final_rainfall_shapefile_updated import run_shapefile_analysis
from data.rainfall_input_from_shapefile_updated import analyze_excel_report
from data.user_upload_rainfall_updated import analyze_uploaded_file

def use_shapefile_workflow(region_type, region_names, years):
    # Normalize input
    region_type = region_type.lower().strip().replace(" ", "_")
    region_list = [r.strip() for r in region_names.split(",") if r.strip()]
    year_str = years.strip()

    # Log inputs
    print("\n📥 Received from form:")
    print("🔹 Region Type:", region_type)
    print("🔹 Region List:", region_list)
    print("🔹 Years:", year_str)

    # Input validation
    if not region_list:
        raise ValueError("❌ No valid regions selected.")
    if not year_str:
        raise ValueError("❌ No valid years selected.")

    # Convert years from string to list of integers
    year_list = [int(y) for y in year_str.split(",") if y.strip().isdigit()]

    # Run analysis
    excel_path = run_shapefile_analysis(
        region_type, region_list, year_list
    )

    # Confirm file created
    if not excel_path or not os.path.exists(excel_path):
        raise FileNotFoundError(f"❌ Excel output not found: {excel_path}")

    print(f"✅ Excel successfully created at: {excel_path}")
    analyze_excel_report(excel_path)

def use_file_upload_workflow():
    print("\n📤 Proceeding with Excel upload and analysis...")

    uploaded_path = os.environ.get("UPLOADED_EXCEL_PATH")
    if uploaded_path and os.path.exists(uploaded_path):
        print(f"📄 File to be analyzed: {uploaded_path}")
        analyze_uploaded_file(uploaded_path)
    else:
        raise FileNotFoundError("❌ No uploaded Excel file found.")
