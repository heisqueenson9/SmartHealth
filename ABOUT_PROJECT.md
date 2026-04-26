# Smart Health Sync — Project Statement and Technical Report

By: **Enock Queenson Eduafo** | Student ID: 11014444  
Supervisor: **Professor Solomon Mensah**  
Institution: **University of Ghana, Department of Computer Science**  
Programme: **Information Technology**  
Year: **2026**

---

## Why I Chose This Topic

I decided to choose disease prediction because health access and diagnostic accuracy are very real challenges in Ghana and across Africa. I've seen how clinics can get overwhelmed, and small details in patient data might get missed when clinicians are under heavy pressure. I wanted to build something that demonstrates how the data we already collect in our health systems can be used for more intelligent decision-making. This project is where my passion for Information Technology meets a real-world problem that affects people's lives at home.

## What I Built

I developed a clinical decision-support prototype called Smart Health Sync. It is a system that can predict six different health conditions by analyzing 24 clinical biomarkers like glucose, cholesterol, and hemoglobin levels. For the engine, I trained and compared four different machine learning classifiers: Random Forest, Support Vector Machine, Decision Tree, and Logistic Regression. I then built a web interface using the Flask framework so a clinician or researcher can input patient data and get an instant prediction with a confidence score and recommended next steps.

## Challenges I Faced and How I Overcame Them

Building the model was not as straightforward as I first thought. I ran into several technical hurdles along the way:

- **Missing Data for Heart Disease**: I found that Heart Disease was originally missing from some parts of the data. I had to combine the different datasets I found and then perform a proper stratified split to ensure that every disease category was represented in both the training and the final testing sets.
- **Handling Class Imbalance**: Heart Disease only had 39 samples in the whole dataset, which made it very hard for the models to learn compared to Diabetes which had over 800. I solved this by using class weight balancing, which tells the algorithm to pay more attention to the minority classes.
- **Choosing the Right Framework**: I spent some time deciding between using Streamlit or Flask for the web app. I eventually chose Flask because it gave me much more control over the custom CSS design and animations, which I wanted to keep professional and modern.
- **Proper Feature Scaling**: I had to make sure the StandardScaler was only fitted on the training data and then applied to the test data. Fitting it on the whole dataset would have caused "data leakage" and gave me misleadingly high accuracy scores.

## What I Would Improve With More Time

If I had more time to continue this research, I would focus on:
- **Collecting More Clinical Data**: Specifically for the Heart Disease and Thrombocytopenia classes to improve their performance further.
- **Explainable AI**: I would love to add SHAP (SHapley Additive exPlanations) values to the results. This would show a clinician exactly which biomarkers were the most important for that specific patient's diagnosis.
- **Raw Input Parsing**: Currently, the system needs pre-normalized numbers. I would build a converter so clinicians can enter raw lab values (like mg/dL) directly.
- **Local Diseases**: I would expand the system to include conditions that are specifically prevalent in West African populations, like malaria or sickle cell disease.

## Relevance to Ghana and Africa

Machine learning in healthcare matters specifically in the Ghanaian context because we have gaps in specialist access, especially in rural areas. As we continue to digitize our health records in hospitals across the country, we have a massive opportunity to use affordable AI-assisted tools to support our primary care doctors. A tool like this isn't meant to replace a doctor, but to act as a second pair of eyes that can process thousands of data points in a second, helping us provide better care for everyone.

---

**Enock Queenson Eduafo**  
Student ID: 11014444  
Department of Computer Science — Information Technology  
University of Ghana  
Supervisor: Professor Solomon Mensah  
2026
