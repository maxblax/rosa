import React from 'react';
import UpcomingAppointments from './UpcomingAppointments';
import BeneficiaryTracking from './BeneficiaryTracking';
import RecentChart from './RecentChart';
import LatestNews from './LatestNews';
import { Plus } from 'lucide-react';

interface HomePageProps {
  onNewInteraction: () => void;
}

const HomePage: React.FC<HomePageProps> = ({ onNewInteraction }) => {
  return (
    <div className="p-6">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold text-gray-800">Tableau de Bord</h1>
        <button 
          onClick={onNewInteraction}
          className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 flex items-center gap-2"
        >
          <Plus size={20} />
          Nouvelle Interaction
        </button>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <UpcomingAppointments />
        <BeneficiaryTracking />
        <RecentChart />
        <LatestNews />
      </div>
    </div>
  );
};

export default HomePage;