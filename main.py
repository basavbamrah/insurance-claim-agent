import os
from dotenv.main import load_dotenv
from langchain_openai import AzureChatOpenAI
from langchain_unstructured import UnstructuredLoader
from unstructured.partition.auto import partition
import nltk
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_openai import OpenAI
from extract import pdf2text
import json
from typing import List

load_dotenv()
os.environ["OPENAI_API_TYPE"] = "azure"

policy_questions = [
    "What is the name of the policy holder?",
    "Name of the Insurer",
    "Policy start/inception date",
    "PED (Pre Existing Disease)",
    "When was first diagnosed?",
    "Whether any treatment/Disease ongoing",
    "Whether that disease will be covered or not?",
    "Waiting period for PED over or not?",
    "Total coverage amount",
    "co-payment",
    "Pre hospitalization days",
    "Any fraud or misrepresentation captured?",
    "Policy running time (from data and to date)",
]

discharge_summary_questions = [
    "Doctors name",
    "Hospital name",
    "Reason for hospitalization",
]


class PolicyQuestion:
    def __init__(self, user: str):
        """
        Initialize PolicyQuestion object.

        Parameters
        ----------
        user : str
            User name of the policy holder
        """

        self.user = user
        self.llm = AzureChatOpenAI(
            openai_api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
            azure_deployment=os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT_NAME"),
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
            temperature=0.8,
            # print(llm.invoke("hello"))
        )

    def __str__(self):
        return self.user

    def read_ocr(self, path: str, file_name: str):
        """
        Read OCR and save it in the docs directory.

        Parameters
        ----------
        path : str
            Path to the document
        file_name : str
            Name of the document
        """

        os.makedirs(f"docs/{self.user}", exist_ok=True)
        loader = UnstructuredLoader(
            path,
            chunking_strategy="basic",
            max_characters=1000,
            include_orig_elements=False,
        )
        data = loader.load()
        additinal_prompt = """"""
        for i in range(len(data)):
            additinal_prompt += data[i].page_content
            additinal_prompt += "\n"
        os.makedirs(f"docs/{self.user}", exist_ok=True)
        with open("docs/" + self.user + f"/{file_name}.txt", "w") as f:
            f.write(additinal_prompt)

        print(f"loaded {file_name}")

    def load_doc(self, path: str, file_name: str):
        """
        Load document and save it in the docs directory.

        Parameters
        ----------
        path : str
            Path to the document
        file_name : str
            Name of the document
        """

        details = pdf2text(path, self.user)

        os.makedirs(f"docs/{self.user}", exist_ok=True)
        with open("docs/" + self.user + f"/{file_name}.txt", "w") as f:
            f.write(details)
        print(f"loaded {file_name}")

    def load_bill(self, path: str):
        """
        Load bill and save it in the docs directory.

        Parameters
        ----------
        path : str
            Path to the bill
        """
        print("loading bill")
        bill_details = pdf2text(path, self.user)
        os.makedirs(f"docs/{self.user}", exist_ok=True)
        with open("docs/" + self.user + "/bill.txt", "w") as f:
            f.write(bill_details)
        print("loaded bill")

    def load_report(self, path: str):
        """
        Load report and save it in the docs directory.

        Parameters
        ----------
        path : str
            Path to the report
        """
        print("loading report")
        report_details = pdf2text(path, self.user)
        os.makedirs(f"docs/{self.user}", exist_ok=True)
        with open("docs/" + self.user + "/report.txt", "w") as f:
            f.write(report_details)
        print("loaded report")

    def get_policy_details(self, path: str, additional_data: str = ""):
        """
        Get policy details from the document.

        Parameters
        ----------
        path : str
            Path to the document
        """
        # if any ongoing treatment/Disease ongoing and first diagnosis is after policy inception date then disease will be covered

        # print("loading policy")
        prompt = f"""You are an expert in Insurance policy assessment.
        You are given a policy document and you need to extract the relevant information and answer the questions.
        
       [important] Note: the total coverage amount of the policy should be calculated including all the premium and bonus etc.

        Always give the answer from the policy document and additional data if given.
        Make sense of the additional data and policy document.
        
        Analyze the policy document and additional data carefully before providing the answer.
        Give reason for the answers 

        if the answer is not in the policy document and additional data then give answer as 'N/A'
        
        additional data:

        {additional_data}

        Policy Document:
        """

        loader = UnstructuredLoader(
            path,
            chunking_strategy="basic",
            max_characters=1000,
            include_orig_elements=False,
        )
        self.data = loader.load()

        additinal_prompt = """"""
        for i in range(len(self.data)):
            additinal_prompt += self.data[i].page_content
            additinal_prompt += "\n"

        prompt = prompt + additinal_prompt + "\n".join(policy_questions)

        suffix = """\n\nAnswer in json format with keys enclosed in double quotes.: 
        {   
            "policy-holder-name": <value>,
            "running-time": <value - running from dd/mm/yyyy to dd/mm/yyyy >,
            "insurer": <value>,
            "start-date": <value>,
            "ped": <value>,
            "first-diagnosis": <value>,
            "ongoing-treatment-disease": <value>,
            "ongoing-disease-covered": <value>,
            "ped-waiting-over": <value>,
            "total-cover-amount": <value>,
            "co-payment": <value>,
            "pre-hospitalization-days": <value>,
            "post-hospitalization-days": <value>,
            "fraud": <value>,
            "remarks": <value- this will be a summary of the policy>,
            "summary-policy-holder": <value: this will be a summary of the policy Holder>
        }"""
        response = self.llm.invoke(prompt + suffix)
        print(response.content)
        response = response.content.replace("```json", "")
        response = response.replace("```", "")
        # response = response.replace("'",'"')

        
        print(response)

        response = json.loads(response, strict=False)
        # print(response.)
        return response

    def get_bill_details(self):
        """
        Get bill details from the document.
        """

        desc = ""
        with open("docs/" + self.user + "/bills.txt", "r") as f:
            desc = f.read()
        prompt = """You are an expert in Insurance policy assessment.
        You are given details of the bill and you need to extract the total of rembursement 
        
        Things to remember:
        1. Give the total of resmbursement (calculate the total of reimbursible items)
        2. Take your time and accurately calculate the total of reimbursible items
        3. Remburseable items are as only the medical expenses like medicines and not non medical expenses
        4. Give the total of reimbursible items and not the total of non reimbursible items saperately also mention the non reimbursible items

        Note: Give your answers very carefully and accurately it is important to give the total of reimbursible items very accurately
        
        Calculate the total very carefully and accurately

        give short and crisp response in English
        give a json response in the following format:
        
        Always enclose the keys in double quotes

        ```json
        {   
            "pharmacy-name": <value>,
            "total": <value>,
            "non-reimbursible": <value>,
            "reimbursible": <value>,
            "deductions": <value- detailed description of non-reimbursible and reimbursible in english only dont create any dictionary for it>,
        }
        ```
        Bill details:
        """ + desc

        additinal_prompt = """"""
        for i in range(len(self.data)):
            additinal_prompt += self.data[i].page_content
            additinal_prompt += "\n"

        prompt = (
            prompt
            + """\n\n for MAXIMUM Reimbursible Amount please check the Policy Document \n\n Policy Document: """
            + additinal_prompt
        )

        response = self.llm.invoke(prompt)
        response = response.content.replace("```json", "")
        response = response.replace("```", "")
        response = response.replace("``", "")
        # response = response.replace("'",'"')
        
        print(response)
        response = json.loads(response, strict=False)
        return response

    def get_discharge_details(self, path: str) -> dict:
        """
        Get discharge summary details from the document.
        """

        desc = ""
        questions = "\n".join(discharge_summary_questions)
        # with open("docs/" + self.user + "/discharge.txt", "r") as f:
        #     desc = f.read()
        loader = UnstructuredLoader(
            path,
            chunking_strategy="basic",
            max_characters=1000,
            include_orig_elements=False,
        )
        data = loader.load()

        additinal_prompt = """"""
        for i in range(len(data)):
            additinal_prompt += data[i].page_content
            additinal_prompt += "\n"

        prompt = (
            f"""You are an expert in Insurance policy assessment.
        You are given details of the discharge summary. You need to answer the following questions
        {questions}

        Things to remember:
        1. Always give the answer in the same order as given in the report
        2. Always give the answer from the report
        3. If the answer is not in the report then give answer as 'N/A'

        
        Discharge summary details:
        """
            + additinal_prompt
            + """
Answer in json format ,        
Always enclose the keys in double quotes

        ```json
        { 
            "doctor-name": <value>,
            "hospital-name": <value>,
            "reason": <value>     
        }
        ```
"""
        )

        response = self.llm.invoke(prompt)
        response = response.content.replace("```json", "")
        response = response.replace("```", "")
        # response = response.replace("'",'"')

        # response = response.replace("``", "")
        
        print(response)

        response = json.loads(response, strict=False)
        # print(response.content)
        return response

    def get_report_details(self, path: str) -> dict:
        """
        Get report details from the document.
        """

        additinal_prompt = ""

        with open("docs/" + self.user + "/reports.txt", "r") as f:
            additinal_prompt = f.read()

        report_questions = "\n".join(["A Brief summary of Report and test conducted on the patient in English", ])
        prompt = (
            f"""You are an expert in Insurance policy assessment.
        You are given details of the report. You need to answer the following questions
        {report_questions}

        Things to remember:
        1. Always give the answer in the same order as given in the report
        2. Always give the answer from the report
        3. If the answer is not in the report then give answer as 'N/A'

        Report details:
        """+ additinal_prompt + """

        Answer in json format , Always enclose  keys in double quotes in your response:

        ```json
        { 
            "reports-tests": <value A comprehensive summary of reports and tests conducted on the patient in English>,
        }
        ```
        """
        )

        response = self.llm.invoke(prompt)
        response = response.content.replace("```json", "")
        response = response.replace("```", "")
        # response = response.replace("``", "")

        print(response)
        response = json.loads(response, strict=False)
        return response

    def get_claim_details(self, file_name: str):
        """
        Get document details from the document.

        Args:
            file_name (str): Name of the document.
            question (str | List): Question to ask the document.
        """
        desc = ""

        with open("docs/" + self.user + "/" + f"{file_name}.txt", "r") as f:
            desc = f.read()

        question = ["what is the total reimbursement sought by the patient?", ]

        # question = "1. give summary of the report in English"
        prompt = f"""You are an expert in Insurance policy assessment.
        You are given details of the claim form. You need to answer the following questions
        {question}
        Things to remember:
        1. Always give the answer in the same order as given in the report
        2. Always give the answer from the report
        3. If the answer is not in the report then give answer as 'N/A'

        Document details:\n
        """ + desc + """\n\nAnswer in json format, Always enclose  keys in double quotes in your response:

        ```json
        { 
            "reimbursement-sought": <value>
        }
        ```
        """

        response = self.llm.invoke(prompt)

        response = response.content.replace("```json", "")
        response = response.replace("```", "")
        # response = response.replace("'",'"')

        # response = response.replace('"', "'")
        
        print(response)
        response = json.loads(response, strict=False)
        # print(response.content)
        return response

    def get_prescription_details(self, file_name: str):
        """
        Get document details from the document.

        Args:
            file_name (str): Name of the document.
            
        """
        desc = ""

        with open("docs/" + self.user + "/" + f"{file_name}.txt", "r") as f:
            desc = f.read()

        question = ["Give the prescription details in English of  medicens along with dose ", ]

        # question = "1. give summary of the report in English"
        prompt = (
            f"""You are an expert in Insurance policy assessment.
        You are given details of the prescription. You need to answer the following questions

        {question}
        Things to remember:
        1. Always give the answer in the same order as given in the report
        2. Always give the answer from the report
        3. If the answer is not in the report then give answer as 'N/A'

        Document details:
        """+ desc + """\n\nAnswer in json format:
        Always enclose the keys in double quotes

        ```json
        { 
            "medicines-prescribed": <value: brief description in English should not be a dictionary>
        }
        ```
        """
        )

        response = self.llm.invoke(prompt)
        response = response.content.replace("```json", "")
        response = response.replace("```", "")
        # response = response.replace("'",'"')
        # response = response.replace('"', "'")
        
        print(response)
        response = json.loads(response, strict=False)
        # print(response.content)
        return response


# obj = PolicyQuestion("user")

# obj.load_bill("docs/bills.pdf")
# # obj.load_doc("docs/Discharge Summary Gangaram.pdf", "discharge_summary")
# # obj.load_doc("docs/bills.pdf", "bill")
# # obj.load_report("docs/report.pdf")

# print("-----------------------------------------------------------")
# print(obj.get_policy_details("docs/policy.pdf"))
# print("-----------------------------------------------------------")
# print(obj.get_discharge_details(path="static/docs/user/discharge.pdf"))
# print("-----------------------------------------------------------")
# print(obj.get_bill_details())
# print("-----------------------------------------------------------")
# print(
#     obj.get_doc_details(
#         "bill", ["1. What is the bill amount?", "2. What is the bill date?"]
#     )
# )
# print("-----------------------------------------------------------")

# print(obj.get_report_details(path="static/docs/None/reports.pdf"))
