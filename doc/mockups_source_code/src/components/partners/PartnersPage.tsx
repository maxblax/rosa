import React, { useState } from 'react';
import { UserPlus } from 'lucide-react';
import PartnersTable from './PartnersTable';
import AddPartnerModal from './AddPartnerModal';

const PartnersPage: React.FC = () => {
  const [isModalOpen, setIsModalOpen] = useState(false);

  return (
    <div className="p-6">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold text-gray-800">Partenaires</h1>
        <button
          onClick={() => setIsModalOpen(true)}
          className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 flex items-center gap-2"
        >
          <UserPlus size={20} />
          Ajouter Partenaire
        </button>
      </div>
      
      <PartnersTable />
      
      <AddPartnerModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
      />
    </div>
  );
};

export default PartnersPage;