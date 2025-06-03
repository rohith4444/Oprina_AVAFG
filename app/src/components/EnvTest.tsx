const EnvTest = () => {
  return (
    <div style={{ background: 'yellow', padding: '10px', margin: '10px' }}>
      <h3>Environment Test:</h3>
      <p>API Key: {import.meta.env.VITE_HEYGEN_API_KEY ? 'LOADED' : 'NOT LOADED'}</p>
      <p>Avatar ID: {import.meta.env.VITE_HEYGEN_AVATAR_ID ? 'LOADED' : 'NOT LOADED'}</p>
      <p>First 10 chars of API key: {import.meta.env.VITE_HEYGEN_API_KEY?.substring(0, 10)}</p>
    </div>
  );
};

export default EnvTest;