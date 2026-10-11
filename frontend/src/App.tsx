import { AppLayout } from './components/layout/AppLayout';
import { DashboardPanel } from './components/dashboard/DashboardPanel';
import { ChatPanel } from './components/chat/ChatPanel';
import { AgentInspector } from './components/inspector/AgentInspector';

import { AuthProvider } from './context/AuthContext';

function App() {
  return (
    <AuthProvider>
      <AppLayout
        dashboard={<DashboardPanel />}
        chat={<ChatPanel />}
        inspector={<AgentInspector />}
      />
    </AuthProvider>
  );
}

export default App;
