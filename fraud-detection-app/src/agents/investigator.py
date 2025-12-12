from .base_agent import BaseAgent

class InvestigatorAgent(BaseAgent):
    def run(self, provider_data):
        """
        Analyzes raw provider data for obvious red flags.
        """
        name = f"{provider_data.get('Prscrbr_First_Name', 'N/A')} {provider_data.get('Prscrbr_Last_Org_Name', 'N/A')}"
        specialty = provider_data.get('specialty', 'N/A')
        
        # Rule-based checks (Simple examples)
        red_flags = []
        if (provider_data.get('cost_per_service') or 0) > 200:
            red_flags.append("Unusually high cost per service exceeding $200 threshold")
        if (provider_data.get('services_per_bene') or 0) > 10:
            red_flags.append("High volume of services per beneficiary (>10)")
            
        # Generate rich HTML summary directly
        if red_flags:
            anomalies_html = "<ul class='space-y-2 mt-2'>\n"
            for flag in red_flags:
                icon = "🚨"
                color_class = "text-red-700 font-semibold"
                anomalies_html += f"<li class='text-sm {color_class}'>{icon} {flag}</li>\n"
            anomalies_html += "</ul>"
            summary_msg = f"<span class='text-red-600 font-bold'>⚠️ {len(red_flags)} anomal{'y' if len(red_flags) == 1 else 'ies'} detected</span>"
            findings_section = f"""
            <div class="bg-orange-50/40 p-3 rounded-lg">
                <h3 class="text-sm font-bold text-slate-700 mb-2">📋 Detailed Findings</h3>
                {anomalies_html}
            </div>
            """
        else:
            anomalies_html = "<p class='text-sm text-green-700'>✅ No rule-based anomalies detected. Billing patterns appear normal.</p>"
            summary_msg = "<span class='text-green-600 font-bold'>✓ No anomalies detected</span>"
            findings_section = f"""
            <div class="bg-green-50/40 p-3 rounded-lg">
                <h3 class="text-sm font-bold text-slate-700 mb-2">📋 Detailed Findings</h3>
                {anomalies_html}
            </div>
            """
        
        investigator_note = f"""
        <div class="space-y-2">
            <div class="bg-purple-50/40 p-3 rounded-lg">
                <h3 class="text-sm font-bold text-slate-700 mb-2">🔍 Anomaly Detection Results</h3>
                <p class="text-sm"><b>Summary:</b> {summary_msg}</p>
                <p class="text-sm"><b>Provider:</b> {name} - {specialty}</p>
                <p class="text-sm"><b>Cost/Service:</b> ${provider_data.get('cost_per_service', 0):.2f} | <b>Services/Beneficiary:</b> {provider_data.get('services_per_bene', 0):.2f}</p>
            </div>
            
            {findings_section}
        </div>
        """
        
        return {
            "agent": "Investigator",
            "name": name,
            "specialty": specialty,
            "red_flags": red_flags,
            "summary": investigator_note
        }
