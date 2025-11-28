from .base_agent import BaseAgent

class SupervisorAgent(BaseAgent):
    def run(self, analyst_output, provider_name, npi):
        """
        Reviews the analysis and recommends a payment action based on risk score and evidence.
        """
        final_score = analyst_output['final_score']
        risk_level = analyst_output['risk_level']
        
        # Rule-based decision logic
        if final_score >= 0.85:
            decision = "STOP PAYMENT"
            confidence = "High"
            reasoning = f"The provider's fraud risk score of {final_score:.4f} is critically high (≥0.85), indicating severe billing anomalies that pose significant financial risk. Immediate payment suspension and comprehensive audit are required."
        elif final_score >= 0.70:
            decision = "HOLD PAYMENT"
            confidence = "High"
            reasoning = f"The provider's fraud risk score of {final_score:.4f} exceeds the high-risk threshold (≥0.70). Payment should be held pending manual review and verification of billing practices to ensure compliance."
        elif final_score >= 0.50:
            decision = "REVIEW REQUIRED"
            confidence = "Medium"
            reasoning = f"The provider's fraud risk score of {final_score:.4f} indicates elevated risk (≥0.50). While not critically high, the billing patterns warrant closer examination before releasing payment. Recommend expedited review of key risk drivers."
        elif final_score >= 0.30:
            decision = "MONITOR"
            confidence = "Medium"
            reasoning = f"The provider's fraud risk score of {final_score:.4f} is slightly elevated but within acceptable range. Recommend continued monitoring and standard compliance checks. Payment can proceed with routine oversight."
        else:
            decision = "RELEASE PAYMENT"
            confidence = "High"
            reasoning = f"The provider's fraud risk score of {final_score:.4f} is low, indicating standard billing patterns consistent with legitimate practice. No anomalies detected that would warrant payment delay. Recommend routine processing."
        
        # Format recommendation as HTML
        if decision == "STOP PAYMENT":
            decision_color = "text-red-600"
            decision_icon = "🛑"
        elif decision == "HOLD PAYMENT":
            decision_color = "text-orange-600"
            decision_icon = "⏸️"
        elif decision == "REVIEW REQUIRED":
            decision_color = "text-yellow-600"
            decision_icon = "⚠️"
        elif decision == "MONITOR":
            decision_color = "text-blue-600"
            decision_icon = "👁️"
        else:
            decision_color = "text-green-600"
            decision_icon = "✅"
        
        recommendation = f"""
        <p class="text-sm mb-2"><b class="{decision_color} text-base">{decision_icon} Decision:</b> <span class="{decision_color} font-bold">{decision}</span></p>
        <p class="text-sm mb-2"><b>Confidence:</b> <span class="font-semibold">{confidence}</span></p>
        <p class="text-sm"><b>Reasoning:</b> {reasoning}</p>
        """
        
        return {
            "agent": "Supervisor",
            "recommendation": recommendation,
            "decision": decision,
            "confidence": confidence
        }
