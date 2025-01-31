from flask import (
    Flask,
    request,
    jsonify,
    render_template,
    redirect,
    flash,
    url_for,
)
from flask_cors import CORS
import requests
import os
from os import urandom
from main import PolicyQuestion
from collections import defaultdict
from werkzeug.datastructures import ImmutableMultiDict
from datetime import datetime
import time
import json

app = Flask(__name__)
CORS(app)

# MySQL Configuration
app.config["SECRET_KEY"] = urandom(24)

@app.route("/")
def index():
    return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        data = request.form
        print(data)
        if data["name"] and data["phone"]:
            print(data["name"], data["phone"])
            res = requests.post(
                "https://20.115.119.223/api/v1/umla/userauth/sendOtp",
                json={"contactNumber": data["phone"]},
                verify=False,
            )
            res = res.json()
            if res["success"]:
                flash("OTP Sent Successfully", "success")
                return redirect(url_for("verify_otp"))
            return redirect(url_for("verify_otp"))
        else:
            flash("Invalid Credentials", "danger")
    return render_template("login.html")


@app.route("/verify-otp", methods=["POST", "GET"])
def verify_otp():
    if request.method == "POST":
        data = request.form
        print(data)
        if data["otp"] and data["phone"]:
            print(
                data["otp"], type(data["otp"]), data["phone"], type(data["phone"])
            )
            res = requests.post(
                "https://20.115.119.223/api/v1/umla/userauth/verifyOtp",
                json={"contactNumber": data["phone"], "otp": int(data["otp"])},
                verify=False,
            )
            res = res.json()
            if res["success"]:
                print(res)
                flash(res["message"], "success")
                user = res["data"]["user"]["_id"]
                return redirect(url_for("home", user=user))
            else:
                print(res)
                flash(res["message"], "danger")
        else:
            print(data)
            flash("Invalid OTP by user", "danger")
    return render_template("verify.html")


@app.route("/home", methods=["GET"])
def home():
    return render_template("index.html")

@app.route("/policy-coverage", methods=["GET", "POST"])
def policy_coverage():
    if request.method == "POST":
        try:
            data = request.form
            file = request.files["file"]
            print("=====================================")
            print(file.filename)
            print(data)
            print("=====================================")
            user = data.get("user")
            result = defaultdict(list)
            
            for key, value in data.items(multi=True):
                result[key].append(value)

            print("=======================================")
            print(result)
            start_data = result["start-date"]
            disease = result["disease"]
            first_diagnosis = result["diagnose-date"]
            drink_smoke = result["drink-smoke"]

            additional_data = f""" the User has provided the following data:
            start date of policy: {start_data}
            whether any ongoing disease : {disease}
            When was ongoing disease first diagnosed: {first_diagnosis}
            Do you drink or smoke? {drink_smoke}
            today's date: {datetime.now().strftime("%Y-%m-%d")}
            """
            print("=======================================")
            print(additional_data)
            os.makedirs(f"static/{user}", exist_ok=True)
            file.save(f"static/{user}_{file.filename}")
            # Process the File
            user_obj = PolicyQuestion(user)
            response = user_obj.get_policy_details(
                f"static/{user}_{file.filename}", additional_data=additional_data
            )
            # Get answers from the File

            # Send the answers to frontend in this format
            answer = {
                "insurer": response["insurer"],
                "start-date": response["start-date"],
                "ped": response["ped"],
                "first-diagnosis": response["first-diagnosis"],
                "ongoing-treatment-disease": response["ongoing-treatment-disease"],
                "ongoing-disease-covered": response["ongoing-disease-covered"],
                "ped-waiting-over": response["ped-waiting-over"],
                "total-cover-amount": response["total-cover-amount"],
                "co-payment": response["co-payment"],
                "pre-hospitalization-days": response["pre-hospitalization-days"],
                "post-hospitalization-days": response["post-hospitalization-days"],
                "fraud": response["fraud"],
                "remarks": response["remarks"],
            }
            return render_template("policy_coverage.html", data=answer, success=True)
        except Exception as e:
            print(e)
            flash(f"Error in Uploading File\n\n{str(e)}", "danger")
            return render_template("policy_coverage.html", success=False, error=str(e))
    return render_template("policy_coverage.html", success=False)


@app.route("/claim-assessment", methods=["GET", "POST"])
def claim_assessment():
    if request.method == "POST":
        try:
            data = request.form
            print("=======================================")
            print(data)
            print("=======================================")
            user = data.get("user")
            docs = json.loads(data.get("docs"))
            if "policy" not in docs or "discharge" not in docs or "bills" not in docs:
                raise Exception("Please Upload all neccessary documents like Policy, Discharge and Bills. Currently uploaded: {}".format(", ".join(docs)))
            user_obj = PolicyQuestion(user)
            result = defaultdict(list)
            for key, value in data.items(multi=True):
                result[key].append(value)

            print("=======================================")
            print(result)
            start_data = result["start-date"]
            disease = result["disease"]
            first_diagnosis = result["diagnose-date"]
            drink_smoke = result["drink-smoke"]

            additional_data = f""" the User has provided the following data:
            start date of policy: {start_data}
            whether any ongoing disease : {disease}
            When was ongoing disease first diagnosed: {first_diagnosis}
            Do you drink or smoke? {drink_smoke}
            today's date: {datetime.now().strftime("%Y-%m-%d")}
            """
            policy_response = user_obj.get_policy_details(f"static/docs/{user}/policy.pdf", additional_data=additional_data)
            bill_response = user_obj.get_bill_details()
            discharge_response = user_obj.get_discharge_details(path=f"static/docs/{user}/discharge.pdf")

            doc_lst = os.listdir(f"static/docs/{user}/")
            lst= [data,
                policy_response,
                bill_response,
                discharge_response ]
            if len(doc_lst) > 3:
                
                for i in doc_lst:
                    if "reports" in i:
                        report_response = user_obj.get_report_details(
                            path=f"static/docs/{user}/reports.pdf"
                        )
                        lst.append(report_response)

                    if "prescriptions" in i:
                        prescription_resp = user_obj.get_prescription_details(
                            file_name="prescriptions",
                        )
                        lst.append(prescription_resp)
                    if "claim" in i:
                        claim_resp = user_obj.get_claim_details(
                            file_name="claim",
                        )
                        lst.append(claim_resp)
            # for any other document if uploaded make a question list and call
            
            # combine all responses into one dict
            response = { 
                k:v for d in lst for k,v in d.items()
            }

            return render_template("claim_assessment.html", data=response, success=True)
        except Exception as e:
            print(e)
            flash(f"Error: {str(e)}", "danger")
            return render_template("claim_assessment.html", success=False, error=str(e))
    return render_template("claim_assessment.html", success=False) 

@app.route("/doc/<document>", methods=["POST"])
def doc(document):
    if request.method == "POST":
        try:
            file = request.files[document]
            data = request.form
            user = data.get("user")
            print("=====================================")
            print(file.filename)
            print(user)
            print("=====================================")
            os.makedirs(f"static/docs/{user}", exist_ok=True)

            file.save(
                f'static/docs/{user}/{document}.{file.filename.split(".")[-1]}'
            )
            if document == "policy" or document == "discharge":
                time.sleep(3)
                flash(f"{document.upper()} Uploaded Successfully", "success")
                return redirect(url_for("claim_assessment"))
            user_obj = PolicyQuestion(user)
            if document == "reports":
                user_obj.read_ocr(
                    f'static/docs/{user}/{document}.{file.filename.split(".")[-1]}',
                    file_name=document,

                )
                flash(f"{document.upper()} Uploaded Successfully", "success")
                return redirect(url_for("claim_assessment"))
            user_obj.load_doc(
                f'static/docs/{user}/{document}.{file.filename.split(".")[-1]}',
                file_name=document,
            )

            flash(f"{document.upper()} Uploaded Successfully", "success")
            return redirect(url_for("claim_assessment"))
        except Exception as e:
            print(e)
            flash(f"Error in Uploading File\n\n{str(e)}", "danger")
            return redirect(url_for("claim_assessment"))


if __name__ == "__main__":
    app.run(debug=True)
