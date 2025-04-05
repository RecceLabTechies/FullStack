import { createContext, type ReactNode, useContext, useState } from 'react';

interface DatabaseOperationsContextType {
  lastUpdated: number;
  triggerRefresh: () => void;
}

const DatabaseOperationsContext = createContext<DatabaseOperationsContextType | undefined>(
  undefined
);

export function DatabaseOperationsProvider({ children }: { children: ReactNode }) {
  const [lastUpdated, setLastUpdated] = useState(Date.now());

  const triggerRefresh = () => {
    setLastUpdated(Date.now());
  };

  return (
    <DatabaseOperationsContext.Provider value={{ lastUpdated, triggerRefresh }}>
      {children}
    </DatabaseOperationsContext.Provider>
  );
}

export function useDatabaseOperations() {
  const context = useContext(DatabaseOperationsContext);
  if (context === undefined) {
    throw new Error('useDatabaseOperations must be used within a DatabaseOperationsProvider');
  }
  return context;
}
