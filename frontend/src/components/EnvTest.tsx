import { useState, useEffect } from 'react';

const EnvTest = () => {
  const [backendStatus, setBackendStatus] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const checkBackend = async () => {
      try {
        // Test backend health
        const healthResponse = await fetch('http://localhost:3001/api/health');
        const healthData = await healthResponse.json();
        
        // Test environment variables
        const envResponse = await fetch('http://localhost:3001/api/test-env');
        const envData = await envResponse.json();
        
        setBackendStatus({
          health: healthData,
          environment: envData,
          connected: true
        });
      } catch (error) {
        setBackendStatus({
          connected: false,
          error: 'Backend not running on port 3001'
        });
      } finally {
        setLoading(false);
      }
    };

    checkBackend();
  }, []);

  if (loading) {
    return (
      <div style={{ background: 'yellow', padding: '10px', margin: '10px' }}>
        <h3>Backend Test:</h3>
        <p>Checking backend connection...</p>
      </div>
    );
  }

  return (
    <div style={{ 
      background: backendStatus?.connected ? 'lightgreen' : 'salmon', 
      padding: '10px', 
      margin: '10px',
      borderRadius: '8px'
    }}>
      <h3>Backend Status:</h3>
      {backendStatus?.connected ? (
        <div>
          <p>✅ Backend: Connected</p>
          <p>✅ API Key: {backendStatus.environment?.api_key_configured ? 'Configured' : 'Missing'}</p>
          <p>🔍 Key Preview: {backendStatus.environment?.api_key_preview}</p>
          <p>📍 Server: {backendStatus.health?.status}</p>
        </div>
      ) : (
        <div>
          <p>❌ Backend: Not Connected</p>
          <p>Error: {backendStatus?.error}</p>
          <p>Make sure to run: npm run server</p>
        </div>
      )}
    </div>
  );
};

export default EnvTest;