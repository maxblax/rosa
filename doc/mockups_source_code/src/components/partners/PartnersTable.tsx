import React, { useState } from 'react';
import { Search, Edit2, Trash2, ChevronDown, ChevronUp } from 'lucide-react';

interface Partner {
  id: number;
  name: string;
  contact: {
    address: string;
    phone: string;
    email: string;
  };
  services: string[];
}

const mockPartners: Partner[] = [
  {
    id: 1,
    name: 'Banque Alimentaire',
    contact: {
      address: '123 Rue de la Solidarité, 75001 Paris',
      phone: '01 23 45 67 89',
      email: 'contact@banquealimentaire.org'
    },
    services: ['Distribution alimentaire', 'Collecte de dons']
  },
  {
    id: 2,
    name: 'Croix Rouge',
    contact: {
      address: '456 Avenue de l\'Entraide, 75002 Paris',
      phone: '01 98 76 54 32',
      email: 'contact@croixrouge.org'
    },
    services: ['Vestiaire social', 'Aide médicale', 'Formation premiers secours']
  },
  {
    id: 3,
    name: 'Restos du Cœur',
    contact: {
      address: '789 Boulevard du Partage, 75003 Paris',
      phone: '01 45 67 89 12',
      email: 'contact@restosducoeur.org'
    },
    services: ['Repas chauds', 'Aide alimentaire', 'Accompagnement social']
  }
];

const PartnersTable: React.FC = () => {
  const [searchTerm, setSearchTerm] = useState('');
  const [sortField, setSortField] = useState<keyof Partner>('name');
  const [sortDirection, setSortDirection] = useState<'asc' | 'desc'>('asc');
  const [selectedServices, setSelectedServices] = useState<string[]>([]);

  const handleSort = (field: keyof Partner) => {
    if (sortField === field) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
    } else {
      setSortField(field);
      setSortDirection('asc');
    }
  };

  const allServices = Array.from(
    new Set(mockPartners.flatMap(partner => partner.services))
  );

  const filteredPartners = mockPartners
    .filter(partner => 
      partner.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      partner.contact.email.toLowerCase().includes(searchTerm.toLowerCase()) ||
      partner.services.some(service => 
        service.toLowerCase().includes(searchTerm.toLowerCase())
      )
    )
    .filter(partner =>
      selectedServices.length === 0 ||
      partner.services.some(service => selectedServices.includes(service))
    );

  const SortIcon = ({ field }: { field: keyof Partner }) => {
    if (sortField !== field) return null;
    return sortDirection === 'asc' ? <ChevronUp size={16} /> : <ChevronDown size={16} />;
  };

  return (
    <div className="bg-white rounded-lg shadow-sm">
      <div className="p-4 border-b border-gray-200">
        <div className="flex flex-col sm:flex-row gap-4">
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" size={20} />
            <input
              type="text"
              placeholder="Rechercher un partenaire..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
            />
          </div>
          <select
            multiple
            value={selectedServices}
            onChange={(e) => {
              const values = Array.from(e.target.selectedOptions, option => option.value);
              setSelectedServices(values);
            }}
            className="border border-gray-300 rounded-lg px-4 py-2 focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
          >
            {allServices.map((service) => (
              <option key={service} value={service}>
                {service}
              </option>
            ))}
          </select>
        </div>
      </div>
      
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th
                className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer"
                onClick={() => handleSort('name')}
              >
                <div className="flex items-center gap-1">
                  Nom du Partenaire
                  <SortIcon field="name" />
                </div>
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Coordonnées
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Services Fournis
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Actions
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {filteredPartners.map((partner) => (
              <tr key={partner.id} className="hover:bg-gray-50">
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="text-sm font-medium text-gray-900">{partner.name}</div>
                </td>
                <td className="px-6 py-4">
                  <div className="text-sm text-gray-900">{partner.contact.address}</div>
                  <div className="text-sm text-gray-500">{partner.contact.phone}</div>
                  <div className="text-sm text-gray-500">{partner.contact.email}</div>
                </td>
                <td className="px-6 py-4">
                  <div className="flex flex-wrap gap-2">
                    {partner.services.map((service) => (
                      <span
                        key={service}
                        className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-indigo-100 text-indigo-800"
                      >
                        {service}
                      </span>
                    ))}
                  </div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                  <div className="flex gap-2">
                    <button
                      className="text-indigo-600 hover:text-indigo-900"
                      onClick={() => console.log('Edit partner:', partner.id)}
                    >
                      <Edit2 size={16} />
                    </button>
                    <button
                      className="text-red-600 hover:text-red-900"
                      onClick={() => console.log('Delete partner:', partner.id)}
                    >
                      <Trash2 size={16} />
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default PartnersTable;