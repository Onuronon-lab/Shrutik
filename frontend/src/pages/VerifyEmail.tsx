import { useEffect, useState } from 'react';
import { useSearchParams, Link } from 'react-router-dom';
import axios from 'axios';

export const VerifyEmail = () => {
  const [searchParams] = useSearchParams();
  const [status, setStatus] = useState<'loading' | 'success' | 'error'>('loading');
  const [message, setMessage] = useState('');
  const token = searchParams.get('token');

  useEffect(() => {
    const verify = async () => {
      try {
        const response = await axios.get(`http://localhost:8000/api/auth/verify-email`, {
          params: { token },
        });

        setStatus('success');
        setMessage(response.data.message);
      } catch (err: any) {
        setStatus('error');
        setMessage(err.response?.data?.detail || 'The link is invalid or has expired.');
      }
    };

    if (token) {
      verify();
    } else {
      setStatus('error');
      setMessage('No verification token found.');
    }
  }, [token]);

  return (
    <div
      style={{
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        minHeight: '80vh',
        textAlign: 'center',
        fontFamily: 'sans-serif',
      }}
    >
      <div
        style={{
          padding: '40px',
          boxShadow: '0 10px 25px rgba(0,0,0,0.05)',
          borderRadius: '12px',
          maxWidth: '450px',
          width: '90%',
          backgroundColor: '#fff',
        }}
      >
        {status === 'loading' && (
          <>
            <h2 style={{ color: '#555' }}>Finalizing Account...</h2>
            <p>Creating your profile on Shrutik Voice Platform.</p>
          </>
        )}

        {status === 'success' && (
          <>
            <div style={{ fontSize: '50px', marginBottom: '20px' }}></div>
            <h2 style={{ color: '#28a745', marginBottom: '10px' }}>Account Created!</h2>
            <p style={{ color: '#666', marginBottom: '25px' }}>{message}</p>
            <Link
              to="/login"
              style={{
                display: 'inline-block',
                backgroundColor: '#007bff',
                color: 'white',
                padding: '12px 24px',
                textDecoration: 'none',
                borderRadius: '6px',
                fontWeight: 'bold',
              }}
            >
              Sign In to Dashboard
            </Link>
          </>
        )}

        {status === 'error' && (
          <>
            <div style={{ fontSize: '50px', marginBottom: '20px' }}></div>
            <h2 style={{ color: '#dc3545', marginBottom: '10px' }}>Verification Failed</h2>
            <p style={{ color: '#666', marginBottom: '25px' }}>{message}</p>
            <Link to="/register" style={{ color: '#007bff', textDecoration: 'underline' }}>
              Return to Registration
            </Link>
          </>
        )}
      </div>
    </div>
  );
};
