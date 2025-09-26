import React, { useState } from 'react';
import { useParams } from 'react-router-dom';
import FinancialTracking from './financial/FinancialTracking';
import PersonalInfo from './PersonalInfo';
import ChildCard from './ChildCard';
import InteractionTimeline from './interactions/InteractionTimeline';

interface Service {
  id: number;
  name: string;
  type: string;
  provider: string;
  isEligible: boolean;
  isActive: boolean;
}

interface Child {
  id: number;
  firstName: string;
  name: string;
  age: number;
  observation: string;
}

const mockServices: Service[] = [
  {
    id: 1,
    name: 'Distribution Alimentaire',
    type: 'Aide Alimentaire',
    provider: 'Banque Alimentaire',
    isEligible: true,
    isActive: true,
  },
  {
    id: 2,
    name: 'Vestiaire Social',
    type: 'Vêtements',
    provider: 'Croix Rouge',
    isEligible: true,
    isActive: false,
  },
  {
    id: 3,
    name: 'Aide au Logement',
    type: 'Logement',
    provider: 'CCAS',
    isEligible: true,
    isActive: false,
  },
];

const mockChildren: Child[] = [
  {
    id: 1,
    firstName: 'Marie',
    name: 'Dupont',
    age: 8,
    observation: 'Excellente élève, participe aux activités périscolaires'
  },
  {
    id: 2,
    firstName: 'Lucas',
    name: 'Dupont',
    age: 5,
    observation: 'Inscrit à la maternelle depuis septembre'
  }
];

const BeneficiaryDetail: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const [services, setServices] = useState(mockServices);
  const [children, setChildren] = useState(mockChildren);
  const [familyStatus, setFamilyStatus] = useState('celibataire');
  const [isEditing, setIsEditing] = useState(false);
  const [housing, setHousing] = useState<string[]>([]);
  const [otherHousing, setOtherHousing] = useState('');

  const toggleService = (serviceId: number) => {
    setServices(services.map(service => 
      service.id === serviceId 
        ? { ...service, isActive: !service.isActive }
        : service
    ));
  };

  const handleChildObservationChange = (childId: number, observation: string) => {
    setChildren(children.map(child =>
      child.id === childId
        ? { ...child, observation }
        : child
    ));
  };

  return (
    <div className="flex gap-6 p-6">
      <div className="w-[65%] space-y-6">
        <PersonalInfo
          isEditing={isEditing}
          onEditToggle={() => setIsEditing(!isEditing)}
          familyStatus={familyStatus}
          onFamilyStatusChange={setFamilyStatus}
          housing={housing}
          onHousingChange={setHousing}
          otherHousing={otherHousing}
          onOtherHousingChange={setOtherHousing}
        />

        <div className="grid grid-cols-2 gap-4">
          {children.map((child) => (
            <ChildCard
              key={child.id}
              name={child.name}
              firstName={child.firstName}
              age={child.age}
              observation={child.observation}
              onObservationChange={(observation) => handleChildObservationChange(child.id, observation)}
              isEditing={isEditing}
            />
          ))}
        </div>

        <FinancialTracking />

        <div className="bg-white rounded-lg shadow-sm p-6">
          <h2 className="text-xl font-semibold mb-4">Services Éligibles</h2>
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Service</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Type</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Prestataire</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Statut</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Action</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {services.map((service) => (
                  <tr key={service.id}>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                      {service.name}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {service.type}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {service.provider}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`px-2 py-1 text-xs font-medium rounded-full ${
                        service.isActive 
                          ? 'bg-green-100 text-green-800'
                          : 'bg-gray-100 text-gray-800'
                      }`}>
                        {service.isActive ? 'Actif' : 'Inactif'}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm">
                      <button
                        onClick={() => toggleService(service.id)}
                        className={`px-3 py-1 rounded-md text-sm font-medium ${
                          service.isActive
                            ? 'bg-red-100 text-red-700 hover:bg-red-200'
                            : 'bg-green-100 text-green-700 hover:bg-green-200'
                        }`}
                      >
                        {service.isActive ? 'Désactiver' : 'Activer'}
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
      
      <div className="w-[35%]">
        <InteractionTimeline />
      </div>
    </div>
  );
};

export default BeneficiaryDetail;