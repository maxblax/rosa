import React, { useState } from 'react';
import { Search, X } from 'lucide-react';

interface BeneficiarySearchDialogProps {
  isOpen: boolean;
  onClose: () => void;
  onSelect: (beneficiaireId: string) => void;
}

interface Beneficiary {
  id: string;
  firstName: string;
  lastName: string;
  email: string;
}

const mockBeneficiaries: Beneficiary[] = [
  { id: '1', firstName: 'Jean', lastName: 'Dupont', email: 'jean.dupont@email.com' },
  { id: '2', firstName: 'Marie', lastName: 'Martin', email: 'marie.martin@email.com' },
  { id: '3', firstName: 'Pierre', lastName: 'Bernard', email: 'pierre.bernard@email.com' },
];

const BeneficiarySearchDialog: React.FC<BeneficiarySearchDialogProps> = ({
  isOpen,
  onClose,
  onSelect,
}) => {
  const [searchQuery, setSearchQuery] = useState('');
  const [filteredBeneficiaries, setFilteredBeneficiaries] = useState<Beneficiary[]>(mockBeneficiaries);

  if (!isOpen) return null;

  const handleSearch = (query: string) => {
    setSearchQuery(query);
    const filtered = mockBeneficiaries.filter(
      (b) =>
        b.firstName.toLowerCase().includes(query.toLowerCase()) ||
        b.lastName.toLowerCase().includes(query.toLowerCase()) ||
        b.email.toLowerCase().includes(query.toLowerCase())
    );
    setFilteredBeneficiaries(filtered);
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-2xl">
        <div className="p-4 border-b border-gray-200 flex justify-between items-center">
          <h2 className="text-lg font-semibold">Rechercher un bénéficiaire</h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-500"
          >
            <X size={20} />
          </button>
        </div>
        
        <div className="p-4">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" size={20} />
            <input
              type="text"
              placeholder="Rechercher par nom, prénom ou email..."
              value={searchQuery}
              onChange={(e) => handleSearch(e.target.value)}
              className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
            />
          </div>
          
          <div className="mt-4 max-h-96 overflow-y-auto">
            {filteredBeneficiaries.map((beneficiary) => (
              <button
                key={beneficiary.id}
                onClick={() => onSelect(beneficiary.id)}
                className="w-full text-left p-3 hover:bg-gray-50 rounded-lg transition-colors flex items-center justify-between"
              >
                <div>
                  <div className="font-medium">
                    {beneficiary.firstName} {beneficiary.lastName}
                  </div>
                  <div className="text-sm text-gray-500">{beneficiary.email}</div>
                </div>
                <div className="text-indigo-600">Sélectionner</div>
              </button>
            ))}
          </div>
        </div>
        
        <div className="p-4 border-t border-gray-200 flex justify-end">
          <button
            onClick={onClose}
            className="px-4 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50"
          >
            Annuler
          </button>
        </div>
      </div>
    </div>
  );
};

export default BeneficiarySearchDialog;