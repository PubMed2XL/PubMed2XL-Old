import io
import os
import uuid
#from pathlib import Path
import pandas as pd
from xml.dom import minidom
from Bio import Medline
import urllib.request as urllib
import requests #substitute of urllib requires installation.
from .forms import GetPMIDsForm
from django.shortcuts import render
from django.http import HttpResponse
from xml.etree import ElementTree
from django.conf import settings
import datetime

API_KEY = settings.NCBI_API_KEY
APP_PATH = os.path.dirname(os.path.abspath(__file__)) # Gets path of the _init_.py file
file_path = os.path.join(APP_PATH, "temp")

n = 300 
medline_text_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pubmed&retmode=text&api_key=" + API_KEY + "&rettype=medline&id=" 
medline_xml_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pubmed&retmode=xml&api_key=" + API_KEY + "&rettype=medline&id=" 
Testing = False
declaration_and_doctype = '''<?xml version="1.0" ?>
<!DOCTYPE PubmedArticleSet PUBLIC "-//NLM//DTD PubMedArticle, 1st January 2019//EN" "https://dtd.nlm.nih.gov/ncbi/pubmed/out/pubmed_190101.dtd">
'''
def faq(request):
    context = {'time': datetime.datetime.now().strftime ("%B %d, %Y")} #October 10, 2020
    template = "pubmed2xl/faq.html"
    return render(request, template, context)

def PubMed2XL(request, pmid):
    context = {}
    template = 'pubmed2xl/index.html'    
    if request.method == "GET":
        initial = ""
        if len(pmid) >=1:
            initial = {"pmids": pmid.replace(" ", "").replace(",", "\r\n")}
        context['form'] = GetPMIDsForm(initial=initial)
    elif request.method == "POST":
        form = GetPMIDsForm(request.POST)
        if form.is_valid():
            pmids = request.POST.get("pmids").strip().split('\r\n')
            batches = [pmids[i * n:(i + 1) * n] for i in range((len(pmids) + n - 1) // n )]
            data = []
            for counter, batch in enumerate(batches):
                k_list = ""
                for pid in batch:
                    if k_list == "":
                        k_list = pid
                    else:
                        k_list = k_list + "," + pid
                URL = medline_text_url + k_list
                text_path = file_path + "/" + str(uuid.uuid1()) + '.txt'
                urllib.urlretrieve(URL, text_path)
                with open(text_path, mode="r", encoding="utf-8") as handle:
                    articles = Medline.parse(handle)
                    for article in articles:
                        data.append(get_all_data(article))
                    handle.close()
                os.remove(text_path)
            print(data)
            df = pd.DataFrame()
            df = df.append(data, True)
            output = io.BytesIO()
            writer = pd.ExcelWriter(output, engine='xlsxwriter')  
            df.to_excel(writer, sheet_name='PubMed2XL', index=False)
            writer.save()
            response = HttpResponse(output.getvalue(), content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
            response['Content-Disposition'] = "attachment; filename=" + str(uuid.uuid1()) + ".xlsx"
            return response
        else:
            context['form'] = form
            return render(request, template, context)
        
    return render(request, template, context)

def download_xml(request, pmid):
    context = {}
    template = 'pubmed2xl/xml.html'    
    if request.method == "GET":
        initial = ""
        if len(pmid) >=1:
            initial = {"pmids": pmid.replace(" ", "").replace(",", "\r\n")}
        context['form'] = GetPMIDsForm(initial=initial)
    elif request.method == "POST":
        form = GetPMIDsForm(request.POST)
        if form.is_valid():
            pmids = request.POST.get("pmids").strip().split('\r\n')
            batches = [pmids[i * n:(i + 1) * n] for i in range((len(pmids) + n - 1) // n )]
            data = None
            for counter, batch in enumerate(batches):
                k_list = ""
                for pid in batch:
                    if k_list == "":
                        k_list = pid
                    else:
                        k_list = k_list + "," + pid
                URL = medline_xml_url + k_list
                tree = get_xml(URL)
                root = tree.getroot()
                #root = tree
                if data == None:
                    data = root
                else:
                    data.extend(root)
            doc = ElementTree.tostring(data).decode('utf-8')
            file = f"{declaration_and_doctype}{doc}"
            response = HttpResponse(file, content_type="application/xml")
            response['Content-Disposition'] = "attachment; filename=" + str(uuid.uuid1()) + ".xml"
            return response
        else:
            context['form'] = form
            return render(request, template, context)
        
    return render(request, template, context)

def get_all_data(article):
    article_data = {}
    article_data["PMID"] = get_data("PMID", article)
    article_data["PMC ID"] = get_data("PMC", article)
    article_data["Title"] = get_data("TI", article)
    article_data["Author(s)"] = get_data("AU", article)
    article_data["Author(s) Full Name"] = get_data("FAU", article)
    article_data["Author(s) Affiliation"] = get_data("AD", article)
    article_data["Corporate Author"] = get_data("CN", article)
    article_data["Collaborator(s)"] = get_data("IR", article)
    article_data["Collaborator(s) Full Name"] = get_data("FIR", article)
    article_data["Collaborator(s) Affiliation"] = get_data("IRAD", article)
    article_data["Source"] = get_data("SO", article)
    article_data["Transliterated Title"] = get_data("TT", article)
    article_data["Journal Title Abbreviation"] = get_data("TA", article)
    article_data["Journal Title"] = get_data("JT", article)
    article_data["ISSN"] = get_data("IS", article)
    article_data["Volume"] = get_data("VI", article)
    article_data["Issue"] = get_data("IP", article)
    article_data["Pages"] = get_data("PG", article)
    article_data["Place of Publication"] = get_data("PL", article)
    abstract = get_data("AB", article)
    if not abstract:
        abstract = ' '.join(article.get("OAB", ""))
    article_data["Abstract"] = abstract
    copyright = get_data("CI", article)
    if not copyright:
        copyright = get_data("OCI", article)
    article_data["Copyright Information"] = copyright
    article_data["Language"] = get_data("LA", article)
    article_data["Publication Type"] = get_data("PT", article)
    article_data["MeSH Terms"] = get_data("MH", article)
    article_data["Grant Number"] = get_data("GR", article)
    article_data["Number of References"] = get_data("RF", article)
    article_data["General Note"] = get_data("GN", article)
    article_data["Date of Publication"] = get_data("DP", article)
    article_data["Date of Electronic Publication"] = get_data("DEP", article)
    article_data["Date Created"] = get_data("DA", article)
    article_data["Date Completed"] = get_data("DCOM", article)
    article_data["Date Revised"] = get_data("LR", article)
    article_data["MeSH Date"] = get_data("MHDA", article)
    article_data["Entrez Date"] = get_data("EDAT", article)
    article_data["Status"] = get_data("STAT", article)
    article_data["Publication Status"] = get_data("PST", article)
    article_data["Publication History Status"] = get_data("PHST", article)
    article_data["Article Identifier"] = get_data("AID", article)
    article_data["NLM Unique ID"] = get_data("IR", article)
    article_data["Location Identifier"] = get_data("LID", article)
    article_data["Manuscript Identifier"] = get_data("MID", article)
    article_data["Secondary Source ID"] = get_data("SI", article)
    article_data["Publishing Model"] = get_data("PUBM", article)
    article_data["Comment on"] = get_data("CON", article)
    article_data["Comment in"] = get_data("CIN", article)
    article_data["Erratum in"] = get_data("EIN", article)
    article_data["Erratum for"] = get_data("EFR", article)
    article_data["Corrected and Republished in"] = get_data("CRI", article)
    article_data["Corrected and Republished from"] = get_data("CRF", article)
    article_data["Owner"] = get_data("OWN", article)
    return article_data

def get_data(element, source):
    value = source.get(element, "")
    if type(value) == list:
        value = '||'.join(value)
    return value

def get_xml(url):
    '''
    Gets source etree and content encoding by given url

    file:// schema is also supported
    '''
    headers = { 'User-Agent' : 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/76.0.3809.100 Safari/537.36' }
    req = urllib.Request(url, None, headers)
    response = urllib.urlopen(req)
    xml_file = ElementTree.parse(response)
    # response = requests.get(url, headers=headers)
    # response.raw.decode_content = True
    # xml_file = ElementTree.fromstring(response.content)
    return xml_file

""" Graveyard:

def download_data(url, text_path):
    #download_data(URL, text_path) # This downloads txt file from pubmed and saves it in text_path
    headers = { 'User-Agent' : 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/76.0.3809.100 Safari/537.36' }
    if Testing:
        url = "https://pubmed2xl.com/static/pubmed2xl/test.txt"
    req = urllib.Request(url, None, headers)
    response = urllib.urlopen(req).read().decode()
    text_file = open(text_path, "w")
    text_file.write(response)
    text_file.close()
    return text_file

    urllib.urlretrieve(URL, output)

"""