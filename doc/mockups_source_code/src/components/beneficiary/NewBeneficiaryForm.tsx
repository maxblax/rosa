import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { ArrowLeft } from 'lucide-react';

interface FormData {
  civility: string;
  firstName: string;
  lastName: string;
  birthDate: string;
  phone: string;
  email: string;
  profession: string;
  domiciliationAddress: string;
  residenceAddress: string;
  housing: string[];
  otherHousing: string;
  familyStatus: string;
  childrenCount: number;
  children: {
    firstName: string;
    lastName: string;
    age: number;
    observation: string;
  }[];
  incomes: {
    category: string;
    items: {
      [key: string]: number;
    };
  }[];
  expenses: {
    category: string;
    items: {
      [key: string]: number;
    };
  }[];
}

const initialFormData: FormData = {
  civility: '',
  firstName: '',
  lastName: '',
  birthDate: '',
  phone: '',
  email: '',
  profession: '',
  domiciliationAddress: '',
  residenceAddress: '',
  housing: [],
  otherHousing: '',
  familyStatus: 'celibataire',
  childrenCount: 0,
  children: [],
  incomes: [
    {
      category: 'Prestations sociales/minimas sociaux',
      items: {
        'RSA/Prime d\'activité': 0,
        'AAH, PI (pension d\'invalidité)': 0,
        'APL (Bailleur ou bénéficiaire)': 0,
        'PAJE': 0,
        'AF (Allocations Familiales)': 0,
        'CF (Complément Familial)': 0,
        'ASF (Allocation de Soutien Familial)': 0,
        'APE Congé Parental': 0
      }
    },
    {
      category: 'Revenus',
      items: {
        'IJ CPAM/MSA': 0,
        'France Travail': 0,
        'Retraite, A.S.P.A.': 0,
        'Salaire': 0,
        'Allocation Demandeur d\'Asile (ADA)': 0,
        'Stage, Formation, bourses': 0,
        'Autres': 0
      }
    },
    {
      category: 'Autres revenus',
      items: {
        'Aide Conseil Départemental': 0,
        'Pension alimentaire': 0,
        'Travail non déclaré': 0,
        'Soutien familial ou amical': 0,
        'Contrat Garantie Jeunes (MLJ)': 0,
        'Contrat d\'apprentissage': 0,
        'Tickets service': 0,
        'Bons d\'alimentation': 0
      }
    }
  ],
  expenses: [
    {
      category: 'Logement',
      items: {
        'Loyer résiduel': 0,
        'Énergie': 0,
        'Eau': 0,
        'Assurance habitation': 0
      }
    },
    {
      category: 'Santé et Éducation',
      items: {
        'Mutuelle privée': 0,
        'CSS (Complémentaire Santé Solidaire)': 0,
        'Frais scolaires (cantine, sorties)': 0,
        'Frais de santé non remboursés': 0
      }
    },
    {
      category: 'Transport',
      items: {
        'Transport en commun': 0,
        'Carburant': 0
      }
    },
    {
      category: 'Engagements financiers',
      items: {
        'Crédit à la consommation': 0,
        'Dettes diverses': 0,
        'Abonnements sport et culture': 0
      }
    }
  ]
};

const housingOptions = [
  { value: 'CADA', label: 'CADA' },
  { value: 'CAO', label: 'CAO' },
  { value: 'CHRS', label: 'CHRS' },
  { value: 'LOGEMENT_DIFFUS', label: 'Logement Diffus' },
  { value: 'COLLECTIF', label: 'Collectif' },
  { value: 'QPV', label: 'Quartier QPV' },
  { value: 'AUTRE', label: 'Autre' }
];

const NewBeneficiaryForm: React.FC = () => {
  const navigate = useNavigate();
  const [formData, setFormData] = useState<FormData>(initialFormData);

  const handleChildrenCountChange = (count: number) => {
    const newCount = Math.max(0, count);
    const currentChildren = [...formData.children];
    
    if (newCount > currentChildren.length) {
      // Add new children
      for (let i = currentChildren.length; i < newCount; i++) {
        currentChildren.push({
          firstName: '',
          lastName: '',
          age: 0,
          observation: ''
        });
      }
    } else if (newCount < currentChildren.length) {
      // Remove excess children
      currentChildren.splice(newCount);
    }

    setFormData(prev => ({
      ...prev,
      childrenCount: newCount,
      children: currentChildren
    }));
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    console.log(formData);
    navigate('/beneficiaires');
  };

  return (
    <div className="flex-1 p-6 bg-gray-50 overflow-auto">
      <div className="max-w-5xl mx-auto">
        <div className="flex items-center gap-4 mb-6">
          <button
            onClick={() => navigate(-1)}
            className="flex items-center gap-2 text-gray-600 hover:text-gray-900"
          >
            <ArrowLeft size={20} />
            Retour
          </button>
          <h1 className="text-2xl font-bold text-gray-800">Nouveau Bénéficiaire</h1>
        </div>

        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Personal Information */}
          <div className="bg-white rounded-lg shadow-sm p-6">
            <h2 className="text-xl font-semibold mb-6">Informations Personnelles</h2>
            <div className="grid grid-cols-2 gap-6">
              <div>
                <label className="block text-sm font-medium text-gray-700">Civilité</label>
                <select
                  value={formData.civility}
                  onChange={e => setFormData(prev => ({ ...prev, civility: e.target.value }))}
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
                >
                  <option value="">Sélectionner...</option>
                  <option value="M.">M.</option>
                  <option value="Mme">Mme</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700">Prénom</label>
                <input
                  type="text"
                  value={formData.firstName}
                  onChange={e => setFormData(prev => ({ ...prev, firstName: e.target.value }))}
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700">Nom</label>
                <input
                  type="text"
                  value={formData.lastName}
                  onChange={e => setFormData(prev => ({ ...prev, lastName: e.target.value }))}
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700">Date de naissance</label>
                <input
                  type="date"
                  value={formData.birthDate}
                  onChange={e => setFormData(prev => ({ ...prev, birthDate: e.target.value }))}
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700">Téléphone</label>
                <input
                  type="tel"
                  value={formData.phone}
                  onChange={e => setFormData(prev => ({ ...prev, phone: e.target.value }))}
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700">Email</label>
                <input
                  type="email"
                  value={formData.email}
                  onChange={e => setFormData(prev => ({ ...prev, email: e.target.value }))}
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700">Métier / Savoir-faire</label>
                <input
                  type="text"
                  value={formData.profession}
                  onChange={e => setFormData(prev => ({ ...prev, profession: e.target.value }))}
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700">Adresse de domiciliation</label>
                <input
                  type="text"
                  value={formData.domiciliationAddress}
                  onChange={e => setFormData(prev => ({ ...prev, domiciliationAddress: e.target.value }))}
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700">Lieu de résidence</label>
                <input
                  type="text"
                  value={formData.residenceAddress}
                  onChange={e => setFormData(prev => ({ ...prev, residenceAddress: e.target.value }))}
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
                />
              </div>

              <div className="col-span-2">
                <label className="block text-sm font-medium text-gray-700 mb-2">Hébergement</label>
                <div className="space-y-2">
                  <div className="flex flex-wrap gap-4">
                    {housingOptions.map((option) => (
                      <label key={option.value} className="inline-flex items-center">
                        <input
                          type="checkbox"
                          value={option.value}
                          checked={formData.housing.includes(option.value)}
                          onChange={(e) => {
                            const value = e.target.value;
                            setFormData(prev => ({
                              ...prev,
                              housing: e.target.checked
                                ? [...prev.housing, value]
                                : prev.housing.filter(h => h !== value)
                            }));
                          }}
                          className="rounded border-gray-300 text-indigo-600 focus:ring-indigo-500"
                        />
                        <span className="ml-2 text-sm text-gray-700">{option.label}</span>
                      </label>
                    ))}
                  </div>
                  {formData.housing.includes('AUTRE') && (
                    <input
                      type="text"
                      value={formData.otherHousing}
                      onChange={e => setFormData(prev => ({ ...prev, otherHousing: e.target.value }))}
                      placeholder="Précisez autre type d'hébergement"
                      className="mt-2 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                    />
                  )}
                </div>
              </div>

              <div className="col-span-2">
                <label className="block text-sm font-medium text-gray-700">Situation Familiale</label>
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
                        checked={formData.familyStatus === status.value}
                        onChange={e => setFormData(prev => ({ ...prev, familyStatus: e.target.value }))}
                        className="form-radio text-indigo-600"
                      />
                      <span className="ml-2 text-sm text-gray-700">{status.label}</span>
                    </label>
                  ))}
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700">Nombre d'enfants à charge</label>
                <input
                  type="number"
                  min="0"
                  value={formData.childrenCount}
                  onChange={e => handleChildrenCountChange(parseInt(e.target.value))}
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
                />
              </div>
            </div>
          </div>

          {/* Children Information */}
          {formData.childrenCount > 0 && (
            <div className="bg-white rounded-lg shadow-sm p-6">
              <h2 className="text-xl font-semibold mb-6">Informations sur les Enfants</h2>
              <div className="grid grid-cols-2 gap-4">
                {formData.children.map((child, index) => (
                  <div key={index} className="bg-gray-50 p-4 rounded-lg border border-gray-200">
                    <div className="space-y-4">
                      <div>
                        <label className="block text-sm font-medium text-gray-700">Prénom</label>
                        <input
                          type="text"
                          value={child.firstName}
                          onChange={e => {
                            const newChildren = [...formData.children];
                            newChildren[index] = { ...child, firstName: e.target.value };
                            setFormData(prev => ({ ...prev, children: newChildren }));
                          }}
                          className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                        />
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-gray-700">Nom</label>
                        <input
                          type="text"
                          value={child.lastName}
                          onChange={e => {
                            const newChildren = [...formData.children];
                            newChildren[index] = { ...child, lastName: e.target.value };
                            setFormData(prev => ({ ...prev, children: newChildren }));
                          }}
                          className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                        />
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-gray-700">Âge</label>
                        <input
                          type="number"
                          min="0"
                          value={child.age}
                          onChange={e => {
                            const newChildren = [...formData.children];
                            newChildren[index] = { ...child, age: parseInt(e.target.value) || 0 };
                            setFormData(prev => ({ ...prev, children: newChildren }));
                          }}
                          className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                        />
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-gray-700">Observations</label>
                        <textarea
                          value={child.observation}
                          onChange={e => {
                            const newChildren = [...formData.children];
                            newChildren[index] = { ...child, observation: e.target.value };
                            setFormData(prev => ({ ...prev, children: newChildren }));
                          }}
                          rows={2}
                          className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                        />
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Financial Information */}
          <div className="bg-white rounded-lg shadow-sm p-6">
            <h2 className="text-xl font-semibold mb-6">Informations Financières</h2>
            
            <div className="space-y-8">
              <div>
                <h3 className="text-lg font-medium mb-4">Revenus</h3>
                {formData.incomes.map((category, categoryIndex) => (
                  <div key={category.category} className="mb-6">
                    <h4 className="font-medium text-gray-700 mb-3">{category.category}</h4>
                    <div className="grid grid-cols-2 gap-4">
                      {Object.entries(category.items).map(([key, value]) => (
                        <div key={key}>
                          <label className="block text-sm font-medium text-gray-700">{key}</label>
                          <div className="mt-1 relative rounded-md shadow-sm">
                            <input
                              type="number"
                              value={value}
                              onChange={e => {
                                const newIncomes = [...formData.incomes];
                                newIncomes[categoryIndex].items[key] = parseFloat(e.target.value) || 0;
                                setFormData(prev => ({ ...prev, incomes: newIncomes }));
                              }}
                              className="block w-full rounded-md border-gray-300 pl-3 pr-12 focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                              placeholder="0"
                            />
                            <div className="absolute inset-y-0 right-0 flex items-center pr-3">
                              <span className="text-gray-500 sm:text-sm">€</span>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                ))}
              </div>

              <div>
                <h3 className="text-lg font-medium mb-4">Charges</h3>
                {formData.expenses.map((category, categoryIndex) => (
                  <div key={category.category} className="mb-6">
                    <h4 className="font-medium text-gray-700 mb-3">{category.category}</h4>
                    <div className="grid grid-cols-2 gap-4">
                      {Object.entries(category.items).map(([key, value]) => (
                        <div key={key}>
                          <label className="block text-sm font-medium text-gray-700">{key}</label>
                          <div className="mt-1 relative rounded-md shadow-sm">
                            <input
                              type="number"
                              value={value}
                              onChange={e => {
                                const newExpenses = [...formData.expenses];
                                newExpenses[categoryIndex].items[key] = parseFloat(e.target.value) || 0;
                                setFormData(prev => ({ ...prev, expenses: newExpenses }));
                              }}
                              className="block w-full rounded-md border-gray-300 pl-3 pr-12 focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                              placeholder="0"
                            />
                            <div className="absolute inset-y-0 right-0 flex items-center pr-3">
                              <span className="text-gray-500 sm:text-sm">€</span>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          <div className="flex justify-end gap-4">
            <button
              type="button"
              onClick={() => navigate(-1)}
              className="px-4 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50"
            >
              Annuler
            </button>
            <button
              type="submit"
              className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700"
            >
              Enregistrer
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default NewBeneficiaryForm;