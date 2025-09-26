import React, { useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { ArrowLeft } from 'lucide-react';

interface FormData {
  type: 'association' | 'external' | 'phone';
  title: string;
  description: string;
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
  type: 'association',
  title: '',
  description: '',
  incomes: [
    {
      category: 'Prestations Sociales',
      items: {
        'RSA': 0,
        'Prime d\'activité': 0,
        'AAH': 0,
        'Pension d\'invalidité': 0,
        'APL': 0,
        'Allocations familiales': 0,
        'Congé parental': 0
      }
    },
    {
      category: 'Revenus Professionnels',
      items: {
        'Salaire': 0,
        'Retraite / ASPA': 0,
        'Indemnités France Travail': 0,
        'Indemnités CPAM/MSA': 0,
        'Allocation demandeur d\'asile': 0,
        'Stage/Formation': 0,
        'Travail informel': 0
      }
    },
    {
      category: 'Soutiens',
      items: {
        'Aide familiale/amicale': 0,
        'Aide conseil départemental': 0,
        'Bons alimentaires': 0
      }
    },
    {
      category: 'Jeunesse et Formation',
      items: {
        'Contrat jeune (MLJ)': 0,
        'Contrat apprentissage': 0
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
        'CSS': 0,
        'Frais scolaires': 0
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
      category: 'Autres Engagements',
      items: {
        'Crédit à la consommation': 0,
        'Dettes diverses': 0,
        'Activités sport/culture': 0,
        'Frais de santé non remboursés': 0
      }
    }
  ]
};

const NewInteractionForm: React.FC = () => {
  const navigate = useNavigate();
  const { beneficiaireId } = useParams<{ beneficiaireId: string }>();
  const [formData, setFormData] = useState<FormData>(initialFormData);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    console.log(formData);
    navigate(beneficiaireId ? `/beneficiaire/${beneficiaireId}` : '/beneficiaires');
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
          <h1 className="text-2xl font-bold text-gray-800">Nouvelle Interaction</h1>
        </div>

        <form onSubmit={handleSubmit} className="space-y-6">
          <div className="bg-white rounded-lg shadow-sm p-6">
            <h2 className="text-xl font-semibold mb-4">Détails de l'Interaction</h2>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700">Type d'interaction</label>
                <select
                  value={formData.type}
                  onChange={e => setFormData(prev => ({ ...prev, type: e.target.value as FormData['type'] }))}
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
                >
                  <option value="association">Entretien à l'association</option>
                  <option value="external">Entretien externe</option>
                  <option value="phone">Entretien téléphonique</option>
                </select>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700">Titre</label>
                <input
                  type="text"
                  value={formData.title}
                  onChange={e => setFormData(prev => ({ ...prev, title: e.target.value }))}
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
                  placeholder="Ex: Demande d'aide alimentaire"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700">Description</label>
                <textarea
                  value={formData.description}
                  onChange={e => setFormData(prev => ({ ...prev, description: e.target.value }))}
                  rows={4}
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
                  placeholder="Décrivez la situation et les observations..."
                />
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow-sm p-6">
            <h2 className="text-xl font-semibold mb-6">Mise à jour Financière</h2>
            
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

export default NewInteractionForm;