import React, { useState } from 'react';
import { Plus, UserPlus } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import BeneficiaryTable from './BeneficiaryTable';
import BeneficiaryFilter from './BeneficiaryFilter';

interface BeneficiaryPageProps {
  onNewInteraction: () => void;
}

const BeneficiaryPage: React.FC<BeneficiaryPageProps> = ({ onNewInteraction }) => {
  const navigate = useNavigate();
  const [filters, setFilters] = useState({
    search: '',
    status: 'all',
  });

  return (
    <div className="p-6">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold text-gray-800">Bénéficiaires</h1>
        <div className="flex gap-3">
          <button
            onClick={() => navigate('/nouveau-beneficiaire')}
            className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 flex items-center gap-2"
          >
            <UserPlus size={20} />
            Nouveau Bénéficiaire
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
      
      <BeneficiaryFilter filters={filters} onFilterChange={setFilters} />
      <BeneficiaryTable filters={filters} />
    </div>
  );
};

export default BeneficiaryPage;