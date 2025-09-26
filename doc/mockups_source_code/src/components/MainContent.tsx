import React from 'react';
import HomePage from './home/HomePage';
import BeneficiaryPage from './beneficiary/BeneficiaryPage';
import VolunteerPage from './volunteer/VolunteerPage';
import AnalysisPage from './analysis/AnalysisPage';
import PartnersPage from './partners/PartnersPage';
import CalendarPage from './calendar/CalendarPage';
import UserProfile from './UserProfile';

interface MainContentProps {
  activeMenu: string;
  onNewInteraction: () => void;
}

const MainContent: React.FC<MainContentProps> = ({ activeMenu, onNewInteraction }) => {
  const renderContent = () => {
    switch (activeMenu) {
      case 'home':
        return <HomePage onNewInteraction={onNewInteraction} />;
      case 'beneficiaire':
        return <BeneficiaryPage onNewInteraction={onNewInteraction} />;
      case 'benevole':
        return <VolunteerPage onNewInteraction={onNewInteraction} />;
      case 'partenaires':
        return <PartnersPage />;
      case 'calendrier':
        return <CalendarPage />;
      case 'analyses':
        return <AnalysisPage />;
      case 'stock':
        return (
          <div className="p-8">
            <h1 className="text-3xl font-bold mb-6">Stock Management</h1>
            <p className="text-gray-600">Manage inventory and supplies.</p>
          </div>
        );
      case 'parametre':
        return (
          <div className="p-8">
            <h1 className="text-3xl font-bold mb-6">Paramètres</h1>
            <p className="text-gray-600">Configure system settings.</p>
          </div>
        );
      default:
        return null;
    }
  };

  return (
    <div className="flex-1 flex flex-col">
      <UserProfile />
      <div className="flex-1 bg-gray-50 overflow-auto">
        {renderContent()}
      </div>
    </div>
  );
};

export default MainContent;