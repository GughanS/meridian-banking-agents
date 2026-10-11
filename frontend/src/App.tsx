import { AppLayout } from './components/layout/AppLayout';
import { DashboardPanel } from './components/dashboard/DashboardPanel';
import { ChatPanel } from './components/chat/ChatPanel';
import { AgentInspector } from './components/inspector/AgentInspector';

import { AuthProvider } from './context/AuthContext';
import { InspectorProvider } from './context/InspectorContext';

function App() {
  return (
    <AuthProvider>
      <InspectorProvider>
        <AppLayout
          dashboard={<DashboardPanel />}
          chat={<ChatPanel />}
          inspector={<AgentInspector />}
        />
      </InspectorProvider>
    </AuthProvider>
  );
}

export default App;

