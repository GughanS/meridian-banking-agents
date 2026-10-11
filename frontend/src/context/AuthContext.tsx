import React, { createContext, useContext, useState, useEffect } from 'react';
import { login } from '../api/client';

export type Persona = 'virat' | 'rohit' | 'mahi';

interface AuthContextType {
  token: string | null;
  persona: Persona;
  switchPersona: (p: Persona) => Promise<void>;
  isLoading: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [token, setToken] = useState<string | null>(null);
  const [persona, setPersona] = useState<Persona>('virat');
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    switchPersona('virat');
  }, []);

  const switchPersona = async (p: Persona) => {
    setIsLoading(true);
    try {
      const email = `${p}@example.com`;
      const data = await login(email);
      setToken(data.access_token);
      setPersona(p);
    } catch (error) {
      console.error('Failed to switch persona', error);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <AuthContext.Provider value={{ token, persona, switchPersona, isLoading }}>
      {children}
    </AuthContext.Provider>
  );
};

// eslint-disable-next-line react-refresh/only-export-components
export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
