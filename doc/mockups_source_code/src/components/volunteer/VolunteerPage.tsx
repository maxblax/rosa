import React, { useState } from 'react';
import { UserPlus, Plus } from 'lucide-react';
import VolunteerTable from './VolunteerTable';
import NewVolunteerModal from './NewVolunteerModal';

interface VolunteerPageProps {
  onNewInteraction: () => void;
}

const VolunteerPage: React.FC<VolunteerPageProps> = ({ onNewInteraction }) => {
  const [isModalOpen, setIsModalOpen] = useState(false);

  return (
    <div className="p-6">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold text-gray-800">Bénévoles</h1>
        <div className="flex gap-3">
          <button
            onClick={() => setIsModalOpen(true)}
            className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 flex items-center gap-2"
          >
            <UserPlus size={20} />
            Nouveau Bénévole
          </button>
          <button 
            onClick={onNewInteraction}
            className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 flex items-center gap-2"
          >
            <Plus size={20} />
            Nouvelle Interaction
          </button>
        </div>
      </div>
      
      <VolunteerTable />
      
      <NewVolunteerModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
      />
    </div>
  );
};

export default VolunteerPage;