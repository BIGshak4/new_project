import { LANDING_REPORTED_COMPANIES } from "../lib/landing-content";

export function LandingCompanyReports({ he, className }: { he: boolean; className?: string }) {
  return (
    <div className={className}>
      <p>{he ? "שאלות מקוריות, לצד שאלות שדווחו מראיונות בחברות כמו:" : "Original practice questions, alongside questions reported from interviews at companies including:"}</p>
      <ul aria-label={he ? "חברות שמופיעות בדיווחי השאלות" : "Companies named in question reports"}>
        {LANDING_REPORTED_COMPANIES.map(company => <li key={company}><bdi dir="ltr">{company}</bdi></li>)}
      </ul>
      <p>{he ? "שיוך החברות מבוסס על דיווחים ואינו מעיד על שיתוף פעולה רשמי." : "Company attribution is based on reports and does not imply an official partnership."}</p>
    </div>
  );
}
