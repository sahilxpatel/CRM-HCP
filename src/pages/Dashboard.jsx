import ChatLogger from "../components/ChatLogger";
import FormLogger from "../components/FormLogger";
import InteractionList from "../components/InteractionList";

const Dashboard = () => {
  return (
    <div className="app-shell">
      <header className="header">
        <div className="title-block">
          <h1>AI-First CRM</h1>
          <p>
            Log, summarize, and follow up with healthcare professionals using a
            structured form or conversational AI.
          </p>
        </div>
        <div className="badge">HCP Interaction Logging</div>
      </header>

      <section className="dashboard-grid">
        <FormLogger />
        <ChatLogger />
        <InteractionList />
      </section>
    </div>
  );
};

export default Dashboard;
