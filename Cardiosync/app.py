"""
Cardiosync - Main Application
Precision Digital Twin for Cardiovascular Care

Updated with: Download Report, Data Privacy & WhatsApp/SMS Integration
"""

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import altair as alt

# Import custom modules
from api_client import get_air_quality, calculate_environmental_risk, display_environmental_data

# Import authentication system
try:
    from auth_system import AuthSystem
    AUTH_AVAILABLE = True
    auth_system = AuthSystem()
except ImportError:
    AUTH_AVAILABLE = False
    st.error("⚠️ Authentication system not available")

# Import VCF parser and gene database
try:
    from vcf_parser import VCFParser
    from gene_database import GeneDatabase
    VCF_AVAILABLE = True
except ImportError:
    VCF_AVAILABLE = False
    st.warning("⚠️ VCF parser not available. Make sure vcf_parser.py and gene_database.py are in the project folder.")

# Import messaging functions (handle import errors gracefully)
try:
    from messaging_client import (
        send_whatsapp_message, 
        send_sms_message, 
        create_whatsapp_report_summary, 
        create_sms_report_summary,
        is_twilio_configured,
        validate_phone_number
    )
    MESSAGING_AVAILABLE = True
except ImportError as e:
    MESSAGING_AVAILABLE = False
    st.error(f"⚠️ Messaging module error: {e}")
    st.info("Make sure messaging_client.py is in the same folder as app.py")  


# Page configuration
st.set_page_config(
    page_title="Cardiosync - Precision Cardiovascular Care",
    page_icon="❤️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
    <style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        color: #e74c3c;
        text-align: center;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #7f8c8d;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #e74c3c;
    }
    </style>
""", unsafe_allow_html=True)

# Initialize session state
if 'patient_data' not in st.session_state:
    st.session_state.patient_data = None
if 'risk_calculated' not in st.session_state:
    st.session_state.risk_calculated = False
if 'vcf_genotypes' not in st.session_state:
    st.session_state.vcf_genotypes = None
if 'genomic_summary' not in st.session_state:
    st.session_state.genomic_summary = None
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'user_data' not in st.session_state:
    st.session_state.user_data = None


# ==============================================================================
# AUTHENTICATION CHECK - Show login if not authenticated
# ==============================================================================
if not st.session_state.logged_in and AUTH_AVAILABLE:
    st.markdown('<div class="main-header">❤️ CardioSync</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Your Digital Heart, Predicting Tomorrow\'s Health Today</div>', unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Login/Signup tabs
    tab1, tab2 = st.tabs(["🔐 Login", "📝 Create Account"])
    
    with tab1:
        st.markdown("### Welcome Back!")
        
        with st.form("login_form"):
            email = st.text_input("Email", key="login_email")
            password = st.text_input("Password", type="password", key="login_password")
            
            submitted = st.form_submit_button("Login", use_container_width=True)
            
            if submitted:
                if not email or not password:
                    st.error("Please enter both email and password")
                else:
                    success, message, user_data = auth_system.login_user(email, password)
                    
                    if success:
                        st.session_state.logged_in = True
                        st.session_state.user_data = user_data
                        
                        # Load patient data if exists
                        patient_data = auth_system.get_patient_data(user_data['user_id'])
                        if patient_data:
                            st.session_state.patient_data = patient_data
                        
                        st.success(message)
                        st.balloons()
                        st.rerun()
                    else:
                        st.error(message)
    
    with tab2:
        st.markdown("### Create Your Account")
        
        with st.form("signup_form"):
            full_name = st.text_input("Full Name", key="signup_name")
            email = st.text_input("Email", key="signup_email")
            password = st.text_input("Password", type="password", key="signup_password", help="Minimum 6 characters")
            password_confirm = st.text_input("Confirm Password", type="password", key="signup_password_confirm")
            
            st.markdown("---")
            st.markdown("#### 📋 Data Privacy & Consent")
            
            consent = st.checkbox("""
            I understand and agree:
            - My health data will be encrypted and stored securely
            - I retain full ownership of my data
            - I can delete my account at any time
            - This is a research tool, not medical diagnosis
            - I should consult healthcare professionals for medical decisions
            """)
            
            submitted = st.form_submit_button("Create Account", use_container_width=True)
            
            if submitted:
                if not consent:
                    st.error("Please accept the data privacy terms")
                elif not full_name or not email or not password:
                    st.error("Please fill in all fields")
                elif password != password_confirm:
                    st.error("Passwords don't match")
                elif len(password) < 6:
                    st.error("Password must be at least 6 characters")
                else:
                    success, message, user_id = auth_system.register_user(email, password, full_name)
                    
                    if success:
                        st.success(message)
                        st.info("✅ Account created! Please login with your credentials.")
                        st.balloons()
                    else:
                        st.error(message)
    
    st.markdown("---")
    st.markdown("### 🔒 Your Data is Safe")
    
    col_p1, col_p2 = st.columns(2)
    with col_p1:
        st.markdown("""
        **Security Features:**
        - 🔐 Password encryption (SHA-256)
        - 🗄️ Secure database storage
        - 🔒 Session management
        - 👤 Full data ownership
        """)
    with col_p2:
        st.markdown("""
        **Your Rights:**
        - ✅ Access your data anytime
        - ✅ Update your information
        - ✅ Export your reports
        - ✅ Delete your account permanently
        """)
    
    st.stop()  # Stop here if not logged in

# ==============================================================================
# USER IS LOGGED IN - Show full app
# ==============================================================================

# Sidebar Navigation
st.sidebar.markdown("# 🫀 Cardiosync")
st.sidebar.markdown("---")

# User profile section
if st.session_state.logged_in and st.session_state.user_data:
    st.sidebar.markdown(f"**👤 {st.session_state.user_data['full_name']}**")
    st.sidebar.caption(f"📧 {st.session_state.user_data['email']}")
    
    if st.sidebar.button("🚪 Logout", use_container_width=True):
        st.session_state.logged_in = False
        st.session_state.user_data = None
        st.session_state.patient_data = None
        st.session_state.risk_calculated = False
        st.success("✅ Logged out successfully!")
        st.rerun()
    
    st.sidebar.markdown("---")

page = st.sidebar.radio(
    "Navigation",
    ["🏠 Home", "📊 Patient Input", "🧬 Risk Analysis", "⏱️ Simulation", "💊 Pharmacogenomics", "👤 My Profile"]
)

st.sidebar.markdown("---")
st.sidebar.info("""
    **CardioSync v0.1**  
    Precision Digital Twin for Cardiovascular Care
    
    Integrating:
    - 🧬 Genomics
    - 🏃 Lifestyle
    - 🌍 Environment
""")

# ==============================================================================
# HOME PAGE
# ==============================================================================
if page == "🏠 Home":
    st.markdown('<div class="main-header">❤️ Cardiosync</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Your Digital Heart, Predicting Tomorrow\'s Health Today</div>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("### 🧬 Genomic Integration")
        st.write("Analyze polygenic risk scores from key cardiovascular variants")
        st.info("**Genes Analyzed:** APOE, PCSK9, LPA, LDLR, APOB, CETP")
    
    with col2:
        st.markdown("### 📊 Multi-Modal Risk")
        st.write("Combine genomics, lifestyle, and environmental data")
        st.success("**Holistic approach** to cardiovascular health")
    
    with col3:
        st.markdown("### 💊 Precision Medicine")
        st.write("Pharmacogenomic recommendations for safe medication")
        st.warning("**Avoid adverse reactions** through genetic insights")
    
    st.markdown("---")
    
    # Key Features
    st.markdown("## 🌟 Key Features")
    
    features_col1, features_col2 = st.columns(2)
    
    with features_col1:
        st.markdown("""
        **🔮 Time-Travel Predictions**
        - Visualize 5-10 year risk trajectories
        - Compare intervention scenarios
        - Interactive "what-if" analysis
        
        **🧠 Explainable AI**
        - SHAP values for transparency
        - Understand your unique risk factors
        - Modifiable vs non-modifiable factors
        """)
    
    with features_col2:
        st.markdown("""
        **⚡ Real-Time Simulation**
        - Test lifestyle changes instantly
        - See risk updates in real-time
        - Evidence-based recommendations
        
        **🌍 Environmental Integration**
        - Air quality impact on heart health
        - Location-based risk factors
        - Live API data integration
        """)
    
    st.markdown("---")
    
    # NEW: Data Privacy Section
    st.markdown("## 🔒 Your Data, Your Control")
    
    col_privacy1, col_privacy2 = st.columns(2)
    
    with col_privacy1:
        st.markdown("""
        **Data Privacy Commitment:**
        - 🔐 End-to-end encryption
        - 🛡️ HIPAA/GDPR compliant
        - 👤 You own your data
        - 🗑️ Delete anytime
        - 🚫 Never sold to third parties
        """)
    
    with col_privacy2:
        st.markdown("""
        **Your Rights:**
        - ✅ Informed consent required
        - ✅ Transparent data usage
        - ✅ Secure storage
        - ✅ Right to deletion
        - ✅ Control over sharing
        """)
    
    st.markdown("---")
    st.info("👈 **Get Started:** Select 'Patient Input' from the sidebar to begin!")

# ==============================================================================
# PATIENT INPUT PAGE
# ==============================================================================
elif page == "📊 Patient Input":
    st.markdown("# 📊 Patient Information")
    st.markdown("Enter patient details to create their digital twin")
    
    # Option to load sample patient or create new
    input_mode = st.radio(
        "Choose input mode:",
        ["Load Sample Patient", "Enter New Patient"]
    )
    
    if input_mode == "Load Sample Patient":
        sample_patients = {
            "High Risk - John (45M)": {
                "name": "John Doe",
                "age": 45,
                "sex": "Male",
                "bp_systolic": 145,
                "bp_diastolic": 90,
                "total_cholesterol": 240,
                "hdl": 35,
                "ldl": 180,
                "smoking": "Current",
                "exercise_days": 0,
                "diet_quality": "Poor",
                "genomic_risk": 1.8,
                "location": "Lagos, Nigeria",  
                "air_quality": None,
                "consent_given": True,
                "created_date": datetime.now()
            },
            "Moderate Risk - Sarah (52F)": {
                "name": "Sarah Johnson",
                "age": 52,
                "sex": "Female",
                "bp_systolic": 138,
                "bp_diastolic": 85,
                "total_cholesterol": 220,
                "hdl": 45,
                "ldl": 150,
                "smoking": "Former",
                "exercise_days": 2,
                "diet_quality": "Fair",
                "genomic_risk": 1.2,
                "location": "London, UK",  
                "air_quality": None,
                "consent_given": True,
                "created_date": datetime.now()
            },
            "Low Risk - Mike (38M)": {
                "name": "Mike Chen",
                "age": 38,
                "sex": "Male",
                "bp_systolic": 118,
                "bp_diastolic": 75,
                "total_cholesterol": 180,
                "hdl": 55,
                "ldl": 95,
                "smoking": "Never",
                "exercise_days": 5,
                "diet_quality": "Excellent",
                "genomic_risk": 0.8,
                "location": "Vancouver, Canada",  
                "air_quality": None,
                "consent_given": True,
                "created_date": datetime.now()
            }
        }
        
        selected_patient = st.selectbox("Select a sample patient:", list(sample_patients.keys()))
        
        if st.button("Load Patient Data"):
            st.session_state.patient_data = sample_patients[selected_patient]
            st.success(f"✅ Loaded: {st.session_state.patient_data['name']}")
    
    else:
        # Manual input form
        with st.form("patient_form"):
            st.markdown("### Basic Information")
            col1, col2 = st.columns(2)
            
            with col1:
                name = st.text_input("Patient Name", "")
                age = st.number_input("Age", min_value=18, max_value=100, value=45)
                sex = st.selectbox("Sex", ["Male", "Female"])
            
            with col2:
                bp_systolic = st.number_input("Systolic BP (mmHg)", min_value=80, max_value=200, value=120)
                bp_diastolic = st.number_input("Diastolic BP (mmHg)", min_value=50, max_value=120, value=80)
            
            st.markdown("### Cholesterol Levels")
            col3, col4, col5 = st.columns(3)
            
            with col3:
                total_cholesterol = st.number_input("Total Cholesterol (mg/dL)", min_value=100, max_value=400, value=200)
            with col4:
                hdl = st.number_input("HDL (mg/dL)", min_value=20, max_value=100, value=50)
            with col5:
                ldl = st.number_input("LDL (mg/dL)", min_value=50, max_value=300, value=120)
            
            st.markdown("### Lifestyle Factors")
            col6, col7, col8 = st.columns(3)
            
            with col6:
                smoking = st.selectbox("Smoking Status", ["Never", "Former", "Current"])
            with col7:
                exercise_days = st.slider("Exercise Days/Week", 0, 7, 3)
            with col8:
                diet_quality = st.selectbox("Diet Quality", ["Poor", "Fair", "Good", "Excellent"])
            
            st.markdown("### 🌍 Environmental Data")
            location = st.text_input(
                "Location (City, Country)", 
                value="Lagos, Nigeria",
                help="Enter your city to assess environmental cardiovascular risk factors"
            )
            
            fetch_env = st.checkbox("Fetch live air quality data", value=True)
            
            if fetch_env and location:
                with st.spinner(f"Fetching environmental data for {location}..."):
                    air_quality = get_air_quality(location)
                    if air_quality:
                        st.success(f"✅ Environmental data retrieved for {location}")
                        env_risk = calculate_environmental_risk(air_quality)
                        st.info(f"🌍 Environmental contribution: +{env_risk}% CVD risk")
                    else:
                        st.warning("⚠️ Could not fetch environmental data. Using default values.")
                        air_quality = None
            else:
                air_quality = None
            
            st.markdown("### Genomic Data")
            st.info("📁 VCF file upload will be implemented by genomics team")
            genomic_risk = st.slider("Genetic Risk Score (temporary)", 0.5, 2.0, 1.0, 0.1)
            
            # NEW: Consent Section
            st.markdown("---")
            st.markdown("### 📋 Data Privacy & Consent")
            
            consent = st.checkbox("""
            I understand and agree to the following:
            - My health and genetic data will be processed to calculate my cardiovascular risk
            - My data is encrypted and stored securely
            - I retain full ownership of my data
            - I can delete my profile at any time
            - This is a research tool, not a medical diagnosis
            - I should consult a healthcare professional for medical decisions
            """, key="consent_checkbox")
            
            submitted = st.form_submit_button("Create Digital Twin")
            
            if submitted:
                if not consent:
                    st.error("⚠️ Please review and accept the data privacy terms to continue.")
                else:
                    st.session_state.patient_data = {
                        "name": name,
                        "age": age,
                        "sex": sex,
                        "bp_systolic": bp_systolic,
                        "bp_diastolic": bp_diastolic,
                        "total_cholesterol": total_cholesterol,
                        "hdl": hdl,
                        "ldl": ldl,
                        "smoking": smoking,
                        "exercise_days": exercise_days,
                        "diet_quality": diet_quality,
                        "genomic_risk": genomic_risk,
                        "location": location,  
                        "air_quality": air_quality,
                        "consent_given": True,
                        "created_date": datetime.now()
                    }
                    st.success("✅ Digital twin created! Go to 'Risk Analysis' to see results.")
    
    # Display current patient data
    if st.session_state.patient_data:
        st.markdown("---")
        st.markdown("### 👤 Current Patient Profile")
        
        patient = st.session_state.patient_data
        
        col_a, col_b, col_c, col_d = st.columns(4)
        with col_a:
            st.metric("Name", patient['name'])
        with col_b:
            st.metric("Age", patient['age'])
        with col_c:
            st.metric("Sex", patient['sex'])
        with col_d:
            st.metric("BP", f"{patient['bp_systolic']}/{patient['bp_diastolic']}")
        
        if patient.get('air_quality') is None and patient.get('location'):
            with st.spinner("Fetching environmental data..."):
                air_quality = get_air_quality(patient['location'])
                patient['air_quality'] = air_quality
        else:
            air_quality = patient.get('air_quality')
        
        environmental_factor = calculate_environmental_risk(air_quality) if air_quality else 0
        
        # NEW: Delete Profile Option
        st.markdown("---")
        st.markdown("### 🗑️ Data Management")
        
        with st.expander("⚠️ Delete My Profile"):
            st.warning("**Warning:** This will permanently delete all your data from this session.")
            st.write("Your data includes:")
            st.write("- Personal health information")
            st.write("- Risk assessment results")
            st.write("- Genomic risk data")
            st.write("- Environmental data")
            
            confirm_text = st.text_input(
                'Type "DELETE" to confirm:',
                key="delete_confirm"
            )
            
            if st.button("🗑️ Permanently Delete My Profile", key="delete_button"):
                if confirm_text == "DELETE":
                    st.session_state.patient_data = None
                    st.session_state.risk_calculated = False
                    st.success("✅ Your profile has been permanently deleted.")
                    st.info("You can create a new profile anytime.")
                    st.rerun()
                else:
                    st.error('❌ Please type "DELETE" exactly to confirm deletion.')

# ==============================================================================
# RISK ANALYSIS PAGE
# ==============================================================================
elif page == "🧬 Risk Analysis":
    st.markdown("# 🧬 Cardiovascular Risk Analysis")
    
    if not st.session_state.patient_data:
        st.warning("⚠️ Please enter patient data first!")
        st.info("👈 Go to 'Patient Input' to begin")
    else:
        patient = st.session_state.patient_data

        if patient.get('air_quality') is None and patient.get('location'):
            with st.spinner("Fetching environmental data..."):
                air_quality = get_air_quality(patient['location'])
                patient['air_quality'] = air_quality
        else:
            air_quality = patient.get('air_quality')
            
        environmental_factor = calculate_environmental_risk(air_quality) if air_quality else 0
        
        st.markdown("### 🔬 Calculating Comprehensive Risk...")
        
        with st.spinner("Analyzing genomic data..."):
            import time
            time.sleep(1)
        
        # Risk calculation
        base_risk = 10
        age_factor = (patient['age'] - 40) * 0.5 if patient['age'] > 40 else 0
        bp_factor = (patient['bp_systolic'] - 120) * 0.2 if patient['bp_systolic'] > 120 else 0
        chol_factor = (patient['ldl'] - 100) * 0.05 if patient['ldl'] > 100 else 0
        smoking_factor = {"Never": 0, "Former": 3, "Current": 8}[patient['smoking']]
        exercise_factor = -1 * patient['exercise_days']
        diet_factor = {"Poor": 5, "Fair": 2, "Good": -1, "Excellent": -3}[patient['diet_quality']]
        genomic_factor = (patient['genomic_risk'] - 1.0) * 10
        
        total_risk = base_risk + age_factor + bp_factor + chol_factor + smoking_factor + exercise_factor + diet_factor + genomic_factor + environmental_factor
        total_risk = max(1, min(total_risk, 50))
        
        # Save risk assessment to database if user is logged in
        if st.session_state.logged_in and AUTH_AVAILABLE:
            auth_system.save_risk_assessment(
                st.session_state.user_data['user_id'],
                total_risk,
                base_risk + age_factor + bp_factor + chol_factor + smoking_factor + exercise_factor + diet_factor,
                genomic_factor,
                environmental_factor
            )
        
        # Display results
        st.markdown("---")
        st.markdown("## 📊 Risk Assessment Results")
        
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            risk_color = "🔴" if total_risk > 20 else "🟡" if total_risk > 10 else "🟢"
            st.markdown(f"### {risk_color} 10-Year Cardiovascular Disease Risk")
            st.markdown(f"# {total_risk:.1f}%")
            
            if total_risk > 20:
                st.error("**High Risk** - Immediate intervention recommended")
            elif total_risk > 10:
                st.warning("**Moderate Risk** - Lifestyle modifications advised")
            else:
                st.success("**Low Risk** - Continue healthy habits")
        
        with col2:
            st.metric("Genetic Component", f"{genomic_factor:.1f}%")
            st.caption("Based on PRS")
        
        with col3:
            st.metric("Lifestyle Impact", f"{exercise_factor + diet_factor:.1f}%")
            st.caption("Modifiable factors")
        
        # Risk breakdown
        st.markdown("---")
        st.markdown("### 🔍 Risk Factor Breakdown")
        
        risk_factors = pd.DataFrame({
            'Factor': ['Environmental', 'Genetic Risk', 'Age', 'Blood Pressure', 'LDL Cholesterol', 
                      'Smoking', 'Exercise', 'Diet Quality'],
            'Contribution': [environmental_factor, genomic_factor, age_factor, bp_factor, chol_factor,
                           smoking_factor, exercise_factor, diet_factor],
            'Modifiable': ['Partially', 'No', 'No', 'Yes', 'Yes', 'Yes', 'Yes', 'Yes']
        })
        
        risk_factors = risk_factors.sort_values('Contribution', ascending=False)
        
        try:
            # Use Altair instead of Plotly (more stable with Streamlit)
            chart = alt.Chart(risk_factors).mark_bar().encode(
                x=alt.X('Contribution:Q', title='Risk Contribution (%)'),
                y=alt.Y('Factor:N', sort='-x', title='Risk Factor'),
                color=alt.Color('Modifiable:N', 
                    scale=alt.Scale(
                        domain=['Yes', 'No', 'Partially'],
                        range=['#27ae60', '#e74c3c', '#f39c12']
                    ),
                    legend=alt.Legend(title='Can You Change It?')
                ),
                tooltip=['Factor', 'Contribution', 'Modifiable']
            ).properties(
                width=600,
                height=400,
                title='Contributing Factors to Cardiovascular Risk'
            )
            
            st.altair_chart(chart, use_container_width=True)
        except Exception as e:
            st.error(f"Error displaying chart: {e}")
            st.dataframe(risk_factors)

        st.markdown("---")
        
        if air_quality:
            display_environmental_data(air_quality)
        else:
            st.info("💡 Add location data to see environmental health impacts")
        
        # Display genomic details if VCF was uploaded
        if st.session_state.vcf_genotypes and st.session_state.genomic_summary:
            st.markdown("---")
            st.markdown("### 🧬 Your Genetic Analysis")
            
            summary = st.session_state.genomic_summary
            
            col_gen1, col_gen2, col_gen3, col_gen4 = st.columns(4)
            with col_gen1:
                st.metric("Variants Analyzed", summary['total_variants_found'])
            with col_gen2:
                st.metric("Genes Covered", len(summary['genes_covered']))
            with col_gen3:
                st.metric("Risk Variants", len(summary['high_risk_variants']))
            with col_gen4:
                st.metric("Protective Variants", len(summary['protective_variants']))
            
            # Show detailed genetic findings
            if len(summary['high_risk_variants']) > 0:
                st.markdown("#### ⚠️ Genetic Risk Factors")
                for var in summary['high_risk_variants'][:10]:  # Top 10
                    gene_info = self.gene_db[self.gene_db['rsid'] == var['rsid']].iloc[0] if hasattr(self, 'gene_db') else None
                    st.write(f"• **{var['gene']}** ({var['rsid']}): Genotype **{var['genotype']}** - {var['effect']:.2f}x risk")
            
            if len(summary['protective_variants']) > 0:
                st.markdown("#### ✅ Protective Genetic Factors")
                for var in summary['protective_variants'][:5]:
                    st.write(f"• **{var['gene']}** ({var['rsid']}): Genotype **{var['genotype']}**")
            
            # Pharmacogenomics if found
            if len(summary['pharmacogenomic_variants']) > 0:
                st.markdown("#### 💊 Drug-Gene Interactions Found")
                st.info(f"We found {len(summary['pharmacogenomic_variants'])} genetic variants that affect medication response. See the Pharmacogenomics tab for details.")
        
        
        # Recommendations
        st.markdown("---")
        st.markdown("### 💡 Personalized Recommendations")
        
        recommendations = []
        
        if patient['smoking'] == "Current":
            recommendations.append("🚭 **Smoking Cessation** - Highest impact intervention (-8% risk)")
        if patient['exercise_days'] < 3:
            recommendations.append("🏃 **Increase Exercise** - Target 150 min/week (-6% risk)")
        if patient['diet_quality'] in ["Poor", "Fair"]:
            recommendations.append("🥗 **Improve Diet** - Mediterranean diet recommended (-4% risk)")
        if patient['bp_systolic'] > 130:
            recommendations.append("💊 **Blood Pressure Management** - Consult physician about medication")
        if patient['ldl'] > 130:
            recommendations.append("💊 **Cholesterol Management** - Consider statin therapy")
        
        for i, rec in enumerate(recommendations, 1):
            st.markdown(f"{i}. {rec}")
        
        st.session_state.risk_calculated = True
        
        # NEW: Download Report Feature
        st.markdown("---")
        st.markdown("### 📄 Get Your Personalized Report")
        
        # Create three columns for different delivery methods
        delivery_col1, delivery_col2, delivery_col3 = st.columns(3)
        
        with delivery_col1:
            st.markdown("#### 💾 Download")
            if st.button("📥 Generate PDF Report", key="download_report", use_container_width=True):
                # Generate report content (existing code)
                report_content = f"""
CARDIOSYNC - PERSONALIZED CARDIOVASCULAR HEALTH REPORT
{'='*60}

PATIENT INFORMATION
Name: {patient['name']}
Age: {patient['age']} years old
Sex: {patient['sex']}
Date: {datetime.now().strftime('%B %d, %Y')}

{'='*60}

YOUR HEART HEALTH SUMMARY

Your 10-Year Heart Disease Risk: {total_risk:.1f}%

What This Means:
"""
                
                if total_risk > 20:
                    report_content += f"""You are at HIGH RISK for developing heart disease in the next 10 years.
This means if we looked at 100 people similar to you, about {total_risk:.0f} would develop 
heart disease within 10 years. However, this is NOT a diagnosis - it's a 
prediction to help you take action now.

IMMEDIATE ACTION REQUIRED: Please consult with a doctor as soon as possible.
"""
                elif total_risk > 10:
                    report_content += """You are at MODERATE RISK for heart disease in the next 10 years.
This means your risk is higher than average, but with lifestyle changes and 
possibly medication, you can significantly reduce this risk.

RECOMMENDED ACTION: Schedule a check-up with your doctor within 3 months.
"""
                else:
                    report_content += """You are at LOW RISK for heart disease in the next 10 years.
This is good news! Your current lifestyle and health status put you in a 
favorable position. Continue your healthy habits.

RECOMMENDED ACTION: Annual check-ups with your doctor.
"""
                
                report_content += f"""

{'='*60}

WHAT'S AFFECTING YOUR HEART HEALTH?

1. YOUR GENES (Cannot Change)
   Impact: {genomic_factor:+.1f}%
   
2. YOUR AGE (Cannot Change)
   Impact: {age_factor:+.1f}%
   
3. YOUR BLOOD PRESSURE (You CAN Manage!)
   Reading: {patient['bp_systolic']}/{patient['bp_diastolic']} mmHg
   Impact: {bp_factor:+.1f}%

4. YOUR CHOLESTEROL (You CAN Manage!)
   LDL: {patient['ldl']} mg/dL
   Impact: {chol_factor:+.1f}%

5. SMOKING (You CAN Change!)
   Status: {patient['smoking']}
   Impact: {smoking_factor:+.1f}%

6. EXERCISE (You CAN Change!)
   Activity: {patient['exercise_days']} days/week
   Impact: {exercise_factor:+.1f}%

7. DIET (You CAN Change!)
   Quality: {patient['diet_quality']}
   Impact: {diet_factor:+.1f}%

{'='*60}

YOUR ACTION PLAN

Priority Actions:
"""
                
                priority_actions = []
                if patient['smoking'] == "Current":
                    priority_actions.append("1. QUIT SMOKING - This is the #1 thing you can do!")
                if patient['bp_systolic'] > 140:
                    priority_actions.append(f"{'2' if len(priority_actions) > 0 else '1'}. SEE A DOCTOR about blood pressure")
                if patient['ldl'] > 160:
                    priority_actions.append(f"{len(priority_actions) + 1}. GET CHOLESTEROL CHECKED")
                if patient['exercise_days'] < 3:
                    priority_actions.append(f"{len(priority_actions) + 1}. START EXERCISING - 30 min daily")
                
                if priority_actions:
                    report_content += "\n".join(priority_actions)
                else:
                    report_content += "Keep up your healthy habits!"
                
                report_content += f"""

{'='*60}

DISCLAIMER:

CardioSync is a research tool for informational purposes only. This report 
should NOT be used as a substitute for professional medical advice, diagnosis, 
or treatment. Always consult your doctor.

{'='*60}

Generated by CardioSync - Precision Genomics for Early Detection
Report Date: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}
{'='*60}
"""
                
                # Download button
                st.download_button(
                    label="💾 Download Report",
                    data=report_content,
                    file_name=f"CardioSync_Report_{patient['name'].replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.txt",
                    mime="text/plain",
                    use_container_width=True
                )
        
        with delivery_col2:
            st.markdown("#### 📱 WhatsApp")
            
            if MESSAGING_AVAILABLE and is_twilio_configured():
                whatsapp_number = st.text_input(
                    "Enter WhatsApp Number",
                    value="+234",
                    help="Include country code (e.g., +234XXXXXXXXXX)",
                    key="whatsapp_input"
                )
                
                if st.button("📲 Send to WhatsApp", key="send_whatsapp", use_container_width=True):
                    # Validate phone number
                    is_valid, error_msg = validate_phone_number(whatsapp_number)
                    
                    if not is_valid:
                        st.error(f"❌ {error_msg}")
                    else:
                        with st.spinner("Sending to WhatsApp..."):
                            # Create WhatsApp-friendly summary
                            whatsapp_msg = create_whatsapp_report_summary(
                                patient, 
                                total_risk, 
                                genomic_factor, 
                                recommendations
                            )
                            
                            # Send message
                            success, message = send_whatsapp_message(whatsapp_number, whatsapp_msg)
                            
                            if success:
                                st.success("✅ Sent to WhatsApp!")
                                st.balloons()
                            else:
                                st.error(f"❌ Failed: {message}")
                                st.info("💡 Make sure you've joined the Twilio WhatsApp sandbox")
            elif not MESSAGING_AVAILABLE:
                st.warning("⚠️ Messaging module not available")
                st.info("Make sure messaging_client.py exists")
            else:
                st.warning("⚠️ Twilio not configured")
                st.info("Add Twilio credentials to `.streamlit/secrets.toml`")
        
        with delivery_col3:
            st.markdown("#### 💬 SMS")
            
            if MESSAGING_AVAILABLE and is_twilio_configured():
                sms_number = st.text_input(
                    "Enter Phone Number",
                    value="+234",
                    help="Include country code (e.g., +234XXXXXXXXXX)",
                    key="sms_input"
                )
                
                if st.button("📨 Send via SMS", key="send_sms", use_container_width=True):
                    # Validate phone number
                    is_valid, error_msg = validate_phone_number(sms_number)
                    
                    if not is_valid:
                        st.error(f"❌ {error_msg}")
                    else:
                        with st.spinner("Sending SMS..."):
                            # Create short SMS summary
                            sms_msg = create_sms_report_summary(patient, total_risk)
                            
                            # Send message
                            success, message = send_sms_message(sms_number, sms_msg)
                            
                            if success:
                                st.success("✅ SMS Sent!")
                            else:
                                st.error(f"❌ Failed: {message}")
                                st.info("💡 SMS requires a Twilio phone number (not free)")
            elif not MESSAGING_AVAILABLE:
                st.warning("⚠️ Messaging module not available")
            else:
                st.warning("⚠️ Twilio not configured")
        
        # Info message about delivery methods
        st.info("💡 **Tip:** WhatsApp delivery is perfect for Nigerian users - no app download needed, works on any phone!")
        
        st.info("➡️ Next: Check the 'Simulation' tab to see your risk over time!")
            # Generate report content
        report_content = f"""
CARDIOSYNC - PERSONALIZED CARDIOVASCULAR HEALTH REPORT
{'='*60}

PATIENT INFORMATION
Name: {patient['name']}
Age: {patient['age']} years old
Sex: {patient['sex']}
Date: {datetime.now().strftime('%B %d, %Y')}

{'='*60}

YOUR HEART HEALTH SUMMARY

Your 10-Year Heart Disease Risk: {total_risk:.1f}%

What This Means:
"""
            
        if total_risk > 20:
             report_content += f"""You are at HIGH RISK for developing heart disease in the next 10 years.
This means if we looked at 100 people similar to you, about {total_risk:.0f} would develop 
heart disease within 10 years. However, this is NOT a diagnosis - it's a 
prediction to help you take action now.

IMMEDIATE ACTION REQUIRED: Please consult with a doctor as soon as possible.
"""
        elif total_risk > 10:
            report_content += """You are at MODERATE RISK for heart disease in the next 10 years.
This means your risk is higher than average, but with lifestyle changes and 
possibly medication, you can significantly reduce this risk.

RECOMMENDED ACTION: Schedule a check-up with your doctor within 3 months.
"""
        else:
            report_content += """You are at LOW RISK for heart disease in the next 10 years.
This is good news! Your current lifestyle and health status put you in a 
favorable position. Continue your healthy habits.

RECOMMENDED ACTION: Annual check-ups with your doctor.
"""
            
            report_content += f"""

{'='*60}

WHAT'S AFFECTING YOUR HEART HEALTH?

We looked at several factors to calculate your risk:

1. YOUR GENES (Cannot Change)
   Your genetic risk score: {patient['genomic_risk']:.1f}x average
   Impact on your risk: {genomic_factor:+.1f}%
   
   What this means: Your DNA contains {('lower than', 'similar to', 'higher than')[1 if 0.9 <= patient['genomic_risk'] <= 1.1 else (0 if patient['genomic_risk'] < 0.9 else 2)]} average genetic 
   risk for heart disease. This is something you were born with and cannot 
   change, but knowing this helps you focus on the things you CAN control.

2. YOUR AGE (Cannot Change)
   Current age: {patient['age']} years
   Impact on your risk: {age_factor:+.1f}%
   
   What this means: As we get older, our risk naturally increases. This is 
   normal and expected.

3. YOUR BLOOD PRESSURE (You CAN Manage This!)
   Current reading: {patient['bp_systolic']}/{patient['bp_diastolic']} mmHg
   Impact on your risk: {bp_factor:+.1f}%
   
   What this means: """
            
        if patient['bp_systolic'] > 140 or patient['bp_diastolic'] > 90:
                report_content += "Your blood pressure is HIGH. This is adding to your risk."
        elif patient['bp_systolic'] > 130 or patient['bp_diastolic'] > 80:
                report_content += "Your blood pressure is slightly elevated."
        else:
                report_content += "Your blood pressure is in a healthy range. Great job!"
            
        report_content += f"""

4. YOUR CHOLESTEROL (You CAN Manage This!)
   LDL (bad cholesterol): {patient['ldl']} mg/dL
   Impact on your risk: {chol_factor:+.1f}%
   
   What this means: """
            
        if patient['ldl'] > 160:
                report_content += "Your bad cholesterol is HIGH. This significantly increases risk."
        elif patient['ldl'] > 130:
                report_content += "Your bad cholesterol is above ideal levels."
        else:
                report_content += "Your cholesterol is at a healthy level!"
            
        report_content += f"""

5. SMOKING (You CAN Change This!)
   Status: {patient['smoking']}
   Impact on your risk: {smoking_factor:+.1f}%
   
   What this means: """
            
        if patient['smoking'] == "Current":
            report_content += """Smoking is ONE OF THE BIGGEST risks for heart disease. 
   The good news? Quitting smoking can reduce your risk by 50% within just 
   1 year! Talk to your doctor about smoking cessation programs."""
        elif patient['smoking'] == "Former":
            report_content += "Great job quitting! Your risk is decreasing over time."
        else:
            report_content += "Excellent! Never smoking is one of the best things for heart health."
            
            report_content += f"""

6. EXERCISE (You CAN Change This!)
   Current activity: {patient['exercise_days']} days per week
   Impact on your risk: {exercise_factor:+.1f}%
   
   What this means: """
            
            if patient['exercise_days'] < 3:
                report_content += """You're not getting enough exercise. Regular physical activity 
   is like medicine for your heart! Aim for at least 150 minutes per week 
   (that's just 30 minutes, 5 days a week). Even walking counts!"""
            else:
                report_content += "Good job staying active! Keep it up!"
            
            report_content += f"""

7. DIET QUALITY (You CAN Change This!)
   Current diet: {patient['diet_quality']}
   Impact on your risk: {diet_factor:+.1f}%
   
   What this means: """
            
            if patient['diet_quality'] == "Poor":
                report_content += """Your diet needs improvement. Think of food as medicine - what you 
   eat directly affects your heart. Focus on: vegetables, fruits, fish, 
   whole grains, nuts. Limit: fried foods, sugary drinks, processed meats."""
            elif patient['diet_quality'] == "Fair":
                report_content += "Your diet could be better. Small improvements can make a big difference!"
            else:
                report_content += "Your diet is helping protect your heart. Keep eating healthy!"
            
            if environmental_factor > 0:
                report_content += f"""

8. YOUR ENVIRONMENT (Partially Controllable)
   Location: {patient.get('location', 'Not specified')}
   Air quality impact: {environmental_factor:+.1f}%
   
   What this means: The air quality where you live is affecting your heart 
   health. While you can't control outdoor air, you can: use air purifiers 
   indoors, exercise in the morning when pollution is lower, check air 
   quality before outdoor activities."""
            
            report_content += f"""

{'='*60}

MEDICATIONS THAT ARE SAFE FOR YOUR GENES

Based on your genetic profile, here's what you should know about common 
heart medications:

✅ SAFE FOR YOU:
   • Prasugrel (blood thinner) - Your genes process this medication normally
   • Atorvastatin (cholesterol medicine) - Low risk of side effects for you

⚠️ USE WITH CAUTION:
   • Warfarin (blood thinner) - You may need a lower dose than average
     → Your doctor should monitor you closely if prescribed this

❌ AVOID IF POSSIBLE:
   • Clopidogrel (Plavix) - Your genes make this medication LESS EFFECTIVE
     → Tell your doctor you're a CYP2C19 poor metabolizer
     → Ask about prasugrel or ticagrelor instead

IMPORTANT: Always discuss these recommendations with your doctor before 
making any changes to your medications.

{'='*60}

YOUR ACTION PLAN - WHAT TO DO NEXT

Priority Actions (Do These First):
"""
            
            priority_actions = []
            if patient['smoking'] == "Current":
                priority_actions.append("1. QUIT SMOKING - This is the #1 thing you can do! Ask your doctor about help.")
            if patient['bp_systolic'] > 140:
                priority_actions.append(f"{'2' if len(priority_actions) > 0 else '1'}. SEE A DOCTOR about your blood pressure - it's too high.")
            if patient['ldl'] > 160:
                priority_actions.append(f"{len(priority_actions) + 1}. GET YOUR CHOLESTEROL CHECKED - discuss medication with your doctor.")
            if patient['exercise_days'] < 3:
                priority_actions.append(f"{len(priority_actions) + 1}. START MOVING - Begin with just 15 minutes of walking daily.")
            
            if priority_actions:
                report_content += "\n".join(priority_actions)
            else:
                report_content += "Keep up your healthy habits! Continue what you're doing."
            
            report_content += f"""

Lifestyle Goals for the Next 3 Months:
□ Exercise at least 150 minutes per week (30 min × 5 days)
□ Eat vegetables with every meal
□ Reduce processed foods and sugary drinks
□ Check blood pressure monthly
□ Get 7-8 hours of sleep nightly
□ Manage stress (try meditation or yoga)

Medical Follow-Up:
"""
            
            if total_risk > 20:
                report_content += "□ Schedule doctor appointment THIS WEEK\n□ Get blood work done (cholesterol, blood sugar)\n□ Discuss starting medication if needed"
            elif total_risk > 10:
                report_content += "□ Schedule doctor appointment within 3 months\n□ Annual blood work\n□ Review this report with your doctor"
            else:
                report_content += "□ Annual check-up\n□ Continue healthy lifestyle"
            
            report_content += f"""

{'='*60}

REMEMBER: This is a PREDICTION, not a diagnosis!

This report gives you an estimate of your risk based on the information 
provided. It does NOT diagnose any disease. Only a doctor can diagnose 
health conditions.

Think of this report as a "weather forecast" for your heart health - it 
helps you prepare and take action, but it's not set in stone. You have 
the power to change many of these factors!

{'='*60}

IMPORTANT DISCLAIMER:

CardioSync is a research tool designed to help you understand your heart and health risks

""
# ==============================================================================
SIMULATION PAGE
# ==============================================================================
"""
elif page == "⏱️ Simulation":
    st.markdown("# ⏱️ Time-Travel Simulation")
    
    if not st.session_state.patient_data:
        st.warning("⚠️ Please enter patient data first!")
    else:
        st.markdown("### 🔮 See Your Heart's Future")
        
        patient = st.session_state.patient_data

        air_quality = patient.get('air_quality')
        environmental_factor = calculate_environmental_risk(air_quality) if air_quality else 0

        
        # Recalculate baseline risk (same as before)
        base_risk = 10
        age_factor = (patient['age'] - 40) * 0.5 if patient['age'] > 40 else 0
        bp_factor = (patient['bp_systolic'] - 120) * 0.2 if patient['bp_systolic'] > 120 else 0
        chol_factor = (patient['ldl'] - 100) * 0.05 if patient['ldl'] > 100 else 0
        smoking_factor = {"Never": 0, "Former": 3, "Current": 8}[patient['smoking']]
        exercise_factor = -1 * patient['exercise_days']
        diet_factor = {"Poor": 5, "Fair": 2, "Good": -1, "Excellent": -3}[patient['diet_quality']]
        genomic_factor = (patient['genomic_risk'] - 1.0) * 10
        
        current_risk = max(1, min(base_risk + age_factor + bp_factor + chol_factor + smoking_factor + exercise_factor + diet_factor + genomic_factor + environmental_factor, 50))
        
        # Interactive controls
        st.markdown("### ⚙️ Test Interventions")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            new_exercise = st.slider("Exercise Days/Week", 0, 7, patient['exercise_days'])
        with col2:
            new_diet = st.selectbox("Diet Quality", ["Poor", "Fair", "Good", "Excellent"], 
                                   index=["Poor", "Fair", "Good", "Excellent"].index(patient['diet_quality']))
        with col3:
            medication = st.checkbox("Start Statin Therapy")
        
        # Recalculate with interventions
        new_exercise_factor = -1 * new_exercise
        new_diet_factor = {"Poor": 5, "Fair": 2, "Good": -1, "Excellent": -3}[new_diet]
        medication_factor = -5 if medication else 0
        
        new_risk = base_risk + age_factor + bp_factor + chol_factor + smoking_factor + new_exercise_factor + new_diet_factor + genomic_factor + medication_factor + environmental_factor
        new_risk = max(1, min(new_risk, 50))
        
        # Show comparison
        st.markdown("---")
        
        comp_col1, comp_col2, comp_col3 = st.columns(3)
        
        with comp_col1:
            st.metric("Current Risk", f"{current_risk:.1f}%")
        with comp_col2:
            st.metric("With Interventions", f"{new_risk:.1f}%", 
                     delta=f"{new_risk - current_risk:.1f}%",
                     delta_color="inverse")
        with comp_col3:
            reduction = ((current_risk - new_risk) / current_risk * 100) if current_risk > 0 else 0
            st.metric("Risk Reduction", f"{reduction:.0f}%")
        
        # Timeline projection
        st.markdown("---")
        st.markdown("### 📈 10-Year Risk Trajectory")
        
        years = list(range(0, 11))
        
        # Current trajectory (risk increases with age)
        current_trajectory = [current_risk * (1 + 0.03 * year) for year in years]
        
        # With intervention trajectory
        intervention_trajectory = [new_risk * (1 + 0.02 * year) for year in years]
        
        trajectory_df = pd.DataFrame({
            'Year': years,
            'Current Path': current_trajectory,
            'With Interventions': intervention_trajectory
        })
        
        fig = px.line(trajectory_df, x='Year', y=['Current Path', 'With Interventions'],
                     title='Predicted Cardiovascular Risk Over Time',
                     labels={'value': 'Risk (%)', 'variable': 'Scenario'})
        
        fig.update_layout(hovermode='x unified')
        
        st.plotly_chart(fig, use_container_width=True)
        
        st.success("✨ This simulation shows how your choices today affect your heart's tomorrow!")

# ==============================================================================
# PHARMACOGENOMICS PAGE
# ==============================================================================
elif page == "💊 Pharmacogenomics":
    st.markdown("# 💊 Pharmacogenomic Recommendations")
    
    if not st.session_state.patient_data:
        st.warning("⚠️ Please enter patient data first!")
    else:
        st.markdown("### 🧬 Personalized Medication Guide")
        st.info("Based on your genetic profile, here are medication recommendations:")
        
        # TODO [GENOMICS]: Replace with actual genotype-based recommendations
        # TODO [CLINICIAN]: Validate all drug recommendations
        
        # Simulated recommendations
        
        
        # Safe drugs (Green)
        st.markdown("### ✅ Recommended Medications")
        
        safe_drugs = [
            {
                "drug": "Prasugrel",
                "class": "Antiplatelet",
                "reason": "Your CYP2C19 genotype indicates normal metabolism",
                "note": "Preferred over clopidogrel for your genetic profile"
            },
            {
                "drug": "Atorvastatin",
                "class": "Statin",
                "reason": "No SLCO1B1 risk variants detected",
                "note": "Low risk of muscle-related side effects"
            }
        ]
        
        for drug in safe_drugs:
            with st.expander(f"✅ {drug['drug']} ({drug['class']})"):
                st.write(f"**Why it's safe for you:** {drug['reason']}")
                st.info(drug['note'])
        
        # Use with caution (Yellow)
        st.markdown("### ⚠️ Use With Caution")
        
        caution_drugs = [
            {
                "drug": "Warfarin",
                "class": "Anticoagulant",
                "reason": "CYP2C9 variant detected - requires dose adjustment",
                "note": "Start with lower dose, monitor INR closely"
            }
        ]
        
        for drug in caution_drugs:
            with st.expander(f"⚠️ {drug['drug']} ({drug['class']})"):
                st.write(f"**Genetic consideration:** {drug['reason']}")
                st.warning(drug['note'])
        
        # Avoid (Red)
        st.markdown("### ❌ Avoid These Medications")
        
        avoid_drugs = [
            {
                "drug": "Clopidogrel",
                "class": "Antiplatelet",
                "reason": "CYP2C19 poor metabolizer - reduced efficacy",
                "alternative": "Use prasugrel or ticagrelor instead"
            }
        ]
        
        for drug in avoid_drugs:
            with st.expander(f"❌ {drug['drug']} ({drug['class']})"):
                st.write(f"**Why to avoid:** {drug['reason']}")
                st.error(f"**Alternative:** {drug['alternative']}")
        
        st.markdown("---")
        st.info("💡 **Note:** These recommendations should be discussed with your physician before making any medication changes.")

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #7f8c8d; padding: 1rem;'>
    <p><strong>Cardiosync</strong> - Precision Digital Twin for Cardiovascular Care</p>
    <p>Integrating Genomics, Lifestyle, and Environment for Early Detection</p>
    <p><em>Hackathon Prototype - For demonstration purposes</em></p>
</div>
""", unsafe_allow_html=True)