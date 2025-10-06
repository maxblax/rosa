import React from 'react';
import { Pencil } from 'lucide-react';

interface PersrosalInfoProps {
  isEditing: boolean;
  onEditToggle: () => void;
  familyStatus: string;
  onFamilyStatusChange: (status: string) => void;
  housing: string[];
  onHousingChange: (housing: string[]) => void;
  otherHousing: string;
  onOtherHousingChange: (value: string) => void;
}

const housingOptions = [
  { value: 'CADA', label: 'CADA' },
  { value: 'CAO', label: 'CAO' },
  { value: 'CHRS', label: 'CHRS' },
  { value: 'LOGEMENT_DIFFUS', label: 'Logement Diffus' },
  { value: 'COLLECTIF', label: 'Collectif' },
  { value: 'QPV', label: 'Quartier QPV' },
  { value: 'AUTRE', label: 'Autre' }
];

const PersrosalInfo: React.FC<PersrosalInfoProps> = ({
  isEditing,
  onEditToggle,
  familyStatus,
  onFamilyStatusChange,
  housing,
  onHousingChange,
  otherHousing,
  onOtherHousingChange
}) => {
  const handleHousingChange = (value: string) => {
    if (housing.includes(value)) {
      onHousingChange(housing.filter(h => h !== value));
    } else {
      onHousingChange([...housing, value]);
    }
  };

  return (
    <div className="bg-white rounded-lg shadow-sm p-6">
      <div className="flex justify-between items-start mb-4">
        <h2 className="text-xl font-semibold">Informations Personnelles</h2>
        <button
          onClick={onEditToggle}
          className="flex items-center gap-2 px-3 py-1 text-sm text-gray-600 hover:text-gray-900 rounded-md hover:bg-gray-100"
        >
          <Pencil size={16} />
          Modifier
        </button>
      </div>
      <div className="grid grid-cols-2 gap-6">
        <div>
          <h3 className="text-sm font-medium text-gray-500">Civilité</h3>
          <p className="mt-1">M.</p>
        </div>
        <div>
          <h3 className="text-sm font-medium text-gray-500">Nom Complet</h3>
          <p className="mt-1">Jean Dupont</p>
        </div>
        <div>
          <h3 className="text-sm font-medium text-gray-500">Métier / Savoir-faire</h3>
          {isEditing ? (
            <input
              type="text"
              defaultValue="Menuisier"
              className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
            />
          ) : (
            <p className="mt-1">Menuisier</p>
          )}
        </div>
        <div>
          <h3 className="text-sm font-medium text-gray-500">Date de Naissance</h3>
          <p className="mt-1">15/06/1985</p>
        </div>
        <div>
          <h3 className="text-sm font-medium text-gray-500">Téléphone</h3>
          <p className="mt-1">06 12 34 56 78</p>
        </div>
        <div>
          <h3 className="text-sm font-medium text-gray-500">Adresse de Domiciliation</h3>
          <p className="mt-1">123 Rue de la République, 75001 Paris</p>
        </div>
        <div>
          <h3 className="text-sm font-medium text-gray-500">Lieu de Résidence</h3>
          <p className="mt-1">123 Rue de la République, 75001 Paris</p>
        </div>
        <div className="col-span-2">
          <h3 className="text-sm font-medium text-gray-500 mb-2">Hébergement</h3>
          <div className="space-y-2">
            <div className="flex flex-wrap gap-4">
              {housingOptions.map((option) => (
                <label key={option.value} className="inline-flex items-center">
                  <input
                    type="checkbox"
                    value={option.value}
                    checked={housing.includes(option.value)}
                    onChange={() => handleHousingChange(option.value)}
                    disabled={!isEditing}
                    className="rounded border-gray-300 text-indigo-600 focus:ring-indigo-500"
                  />
                  <span className="ml-2 text-sm text-gray-700">{option.label}</span>
                </label>
              ))}
            </div>
            {housing.includes('AUTRE') && (
              <input
                type="text"
                value={otherHousing}
                onChange={(e) => onOtherHousingChange(e.target.value)}
                disabled={!isEditing}
                placeholder="Précisez autre type d'hébergement"
                className="mt-2 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
              />
            )}
          </div>
        </div>
        <div className="col-span-2">
          <h3 className="text-sm font-medium text-gray-500">Situation Familiale</h3>
          <div className="mt-2 space-x-4">
            {[
              { value: 'celibataire', label: 'Célibataire' },
              { value: 'marie', label: 'Marié(e)' },
              { value: 'veuf', label: 'Veuf/Veuve' },
              { value: 'vie_maritale', label: 'Vie maritale' },
              { value: 'divorce', label: 'Divorcé(e)' },
              { value: 'separe', label: 'Séparé(e)' }
            ].map((status) => (
              <label key={status.value} className="inline-flex items-center">
                <input
                  type="radio"
                  name="familyStatus"
                  value={status.value}
                  checked={familyStatus === status.value}
                  onChange={(e) => onFamilyStatusChange(e.target.value)}
                  disabled={!isEditing}
                  className="form-radio text-indigo-600"
                />
                <span className="ml-2 text-sm text-gray-700">{status.label}</span>
              </label>
            ))}
          </div>
        </div>
        <div>
          <h3 className="text-sm font-medium text-gray-500">Nombre d'Enfants à Charge</h3>
          <p className="mt-1">2</p>
        </div>
      </div>
    </div>
  );
};

export default PersrosalInfo;