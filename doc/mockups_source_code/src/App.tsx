import React, { useState } from 'react';
import { BrowserRouter as Router, Routes, Route, useNavigate } from 'react-router-dom';
import Sidebar from './components/Sidebar';
import MainContent from './components/MainContent';
import BeneficiaryDetail from './components/beneficiary/BeneficiaryDetail';
import NewBeneficiaryForm from './components/beneficiary/NewBeneficiaryForm';
import NewInteractionForm from './components/interactions/NewInteractionForm';
import BeneficiarySearchDialog from './components/interactions/BeneficiarySearchDialog';

const AppContent = () => {
  const [activeMenu, setActiveMenu] = useState('home');
  const [isSearchDialogOpen, setIsSearchDialogOpen] = useState(false);
  const navigate = useNavigate();

  const handleMenuSelect = (menuId: string) => {
    setActiveMenu(menuId);
    switch (menuId) {
      case 'home':
        navigate('/');
        break;
      case 'beneficiaire':
        navigate('/beneficiaires');
        break;
      case 'partenaires':
        navigate('/partenaires');
        break;
      case 'analyses':
        navigate('/analyses');
        break;
      case 'stock':
        navigate('/stock');
        break;
      case 'parametre':
        navigate('/parametres');
        break;
    }
  };

  return (
    <div className="flex min-h-screen bg-gray-100">
      <Sidebar onMenuSelect={handleMenuSelect} />
      <Routes>
        <Route path="/beneficiaire/:id" element={<BeneficiaryDetail />} />
        <Route path="/nouveau-beneficiaire" element={<NewBeneficiaryForm />} />
        <Route path="/nouvelle-interaction/:beneficiaireId?" element={<NewInteractionForm />} />
        <Route path="*" element={
          <MainContent 
            activeMenu={activeMenu}
            onNewInteraction={() => setIsSearchDialogOpen(true)}
          />
        } />
      </Routes>
      
      <BeneficiarySearchDialog
        isOpen={isSearchDialogOpen}
        onClose={() => setIsSearchDialogOpen(false)}
        onSelect={(beneficiaireId) => {
          setIsSearchDialogOpen(false);
          navigate(`/nouvelle-interaction/${beneficiaireId}`);
        }}
      />
    </div>
  );
};

function App() {
  return (
    <Router>
      <AppContent />
    </Router>
  );
}

export default App;