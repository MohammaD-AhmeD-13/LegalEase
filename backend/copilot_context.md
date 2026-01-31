# LegalEase – Copilot System Context

This repository contains the backend for **LegalEase**, an academic MVP project
developed as part of a BS Data Science Final Year Project.

Copilot MUST follow this document strictly when generating code, logic, or suggestions.

---

## 1. PROJECT OVERVIEW

LegalEase is a **bilingual (Urdu + English), AI-powered legal assistant**
designed for **Pakistan**.

The goal of LegalEase is to:
- Help users understand Pakistani legal documents
- Simplify complex legal language
- Identify risky clauses
- Generate basic legal documents using templates

⚠️ LegalEase does **NOT** provide binding legal advice.

---

## 2. PROJECT STATUS

- This is an **MVP**
- Focus is academic + demonstrational
- Performance and correctness > feature richness
- No production scaling required at this stage

---

## 3. LEGAL DOMAIN SCOPE (STRICT)

LegalEase ONLY covers:

1. Business / Corporate Law  
2. Contract Law  
3. Tax Law  
4. Employment / Labour Law  

All legal reasoning MUST be based on **Pakistani law only**.

### Authoritative Legal Sources (ONLY THESE)

The system is allowed to reference ONLY these statutes:

- Contract Act, 1872
- Companies Act, 2017
- Income Tax Ordinance, 2001
- Industrial Relations Act, 2012

These laws have been converted into plain text files and stored locally.

❌ No foreign law  
❌ No case law (for MVP)  
❌ No commentaries  
❌ No legal blogs  

---

## 4. DATASET PHILOSOPHY

LegalEase uses **Retrieval-Augmented Generation (RAG)**.

### Important Constraints
- NO model training
- NO fine-tuning
- NO rule-based legal reasoning
- NO autonomous legal decision-making

The LLM may ONLY:
- Explain text
- Rephrase content
- Highlight risks
- Summarize obligations

---

## 5. DATASET STRUCTURE (MANDATORY)

All laws are normalized into **ONE unified dataset**: