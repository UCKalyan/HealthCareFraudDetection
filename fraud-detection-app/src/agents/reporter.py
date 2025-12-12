from .base_agent import BaseAgent
from datetime import datetime

class ReporterAgent(BaseAgent):
    def run(self, investigator_output, analyst_output, supervisor_output, npi):
        """
        Synthesizes findings from all agents into a final report.
        """
        system_prompt = self.llm_config['reporter_system_prompt']
        
        # Get current date in a nice format
        current_date = datetime.now().strftime("%B %d, %Y")
        
        user_prompt = self.llm_config['reporter_user_prompt_template'].format(
            npi=npi,
            current_date=current_date,
            investigator_report=investigator_output['summary'],
            analyst_report=analyst_output['analysis_text'],
            supervisor_report=supervisor_output['recommendation']
        )
        
        report_html = self._call_llm(user_prompt, system_prompt)
        
        return {
            "agent": "Reporter",
            "final_narrative": report_html
        }
