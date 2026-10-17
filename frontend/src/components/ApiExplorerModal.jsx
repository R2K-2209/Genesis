import React, { useState, useEffect } from 'react';
import {
  Code2,
  Search,
  Send,
  X,
  ExternalLink,
  Layers,
  CheckCircle2,
  AlertCircle,
  AlertTriangle,
  Copy,
  Clock,
  Sparkles,
  RefreshCw,
  RotateCcw,
  Zap,
  Table,
  Play,
  Check,
  Terminal,
  MessageSquare,
  ChevronRight
} from 'lucide-react';
import { fetchApiCatalog, executeApiEndpoint, updateDriftState } from '../services/api';

const DEFAULT_EXAMPLES = {
  'simple-students': [
    {
      id: 'ex-students-1',
      label: 'Active Enrolled Students',
      badge: 'Enrolled',
      description: 'Retrieves currently enrolled active students with limit 5',
      params: { status: 'enrolled', page: 1, limit: 5 },
      command: 'curl -X GET "http://localhost:8000/api/v1/students/list?status=enrolled&limit=5"',
      prompt: 'Show me a list of active enrolled students'
    },
    {
      id: 'ex-students-2',
      label: 'Graduated Alumni Roster',
      badge: 'Graduated',
      description: 'Lists recently graduated alumni records from students table',
      params: { status: 'graduated', page: 1, limit: 5 },
      command: 'curl -X GET "http://localhost:8000/api/v1/students/list?status=graduated&limit=5"',
      prompt: 'List recently graduated university alumni'
    },
    {
      id: 'ex-students-3',
      label: 'Withdrawn / Inactive Records',
      badge: 'Withdrawn',
      description: 'Inspects withdrawn or suspended student accounts',
      params: { status: 'withdrawn', page: 1, limit: 5 },
      command: 'curl -X GET "http://localhost:8000/api/v1/students/list?status=withdrawn&limit=5"',
      prompt: 'Find withdrawn student accounts'
    }
  ],
  'simple-courses': [
    {
      id: 'ex-courses-1',
      label: 'Calculus Courses (1+ Credits)',
      badge: 'Calculus',
      description: 'Search for university calculus courses offering at least 1 credit',
      params: { search: 'Calculus', min_credits: 1, limit: 5 },
      command: 'curl -X GET "http://localhost:8000/api/v1/courses/catalog?search=Calculus&min_credits=1&limit=5"',
      prompt: 'Search for Calculus courses with at least 1 credit'
    },
    {
      id: 'ex-courses-2',
      label: 'Advanced Statistics (3+ Credits)',
      badge: 'Statistics',
      description: 'Query advanced 3+ credit courses in statistics and quantitative methods',
      params: { search: 'Statistics', min_credits: 3, limit: 5 },
      command: 'curl -X GET "http://localhost:8000/api/v1/courses/catalog?search=Statistics&min_credits=3&limit=5"',
      prompt: 'Find 3-credit statistics courses in the catalog'
    },
    {
      id: 'ex-courses-3',
      label: 'Ethics & Seminar Classes',
      badge: 'Ethics',
      description: 'Filter courses in professional ethics, bioethics, and humanities',
      params: { search: 'Ethics', min_credits: 1, limit: 5 },
      command: 'curl -X GET "http://localhost:8000/api/v1/courses/catalog?search=Ethics&min_credits=1&limit=5"',
      prompt: 'Search for ethics courses in the catalog'
    }
  ],
  'simple-books': [
    {
      id: 'ex-books-1',
      label: 'Physics Library Holdings',
      badge: 'Physics',
      description: 'Searches campus library catalog for physics and sciences literature',
      params: { query: 'Physics', limit: 5 },
      command: 'curl -X GET "http://localhost:8000/api/v1/books/search?query=Physics&limit=5"',
      prompt: 'Search for Physics books in the library'
    },
    {
      id: 'ex-books-2',
      label: 'History & World Studies',
      badge: 'History',
      description: 'Finds world history and social studies textbooks in inventory',
      params: { query: 'History', limit: 5 },
      command: 'curl -X GET "http://localhost:8000/api/v1/books/search?query=History&limit=5"',
      prompt: 'Find History titles in the university library'
    },
    {
      id: 'ex-books-3',
      label: 'Biology & Life Sciences',
      badge: 'Biology',
      description: 'Locates biological sciences and medicine publications',
      params: { query: 'Biology', limit: 5 },
      command: 'curl -X GET "http://localhost:8000/api/v1/books/search?query=Biology&limit=5"',
      prompt: 'Search library books on Biology'
    }
  ],
  'simple-departments': [
    {
      id: 'ex-depts-1',
      label: 'All Academic Departments',
      badge: 'All Depts',
      description: 'Full directory of university colleges, faculties, and codes',
      params: {},
      command: 'curl -X GET "http://localhost:8000/api/v1/departments/list"',
      prompt: 'List all academic departments and their codes'
    },
    {
      id: 'ex-depts-2',
      label: 'Faculty Headcount Check',
      badge: 'Faculties',
      description: 'Overview of academic divisions currently active on campus',
      params: {},
      command: 'curl -X GET "http://localhost:8000/api/v1/departments/list"',
      prompt: 'What faculties and departments does the university have?'
    }
  ],
  'simple-clubs': [
    {
      id: 'ex-clubs-1',
      label: 'Top 5 Student Clubs',
      badge: 'Top 5',
      description: 'Lists top student clubs and registered student organizations',
      params: { limit: 5 },
      command: 'curl -X GET "http://localhost:8000/api/v1/clubs/directory?limit=5"',
      prompt: 'List registered student clubs and organizations'
    },
    {
      id: 'ex-clubs-2',
      label: 'Campus Societies (15 Clubs)',
      badge: '15 Clubs',
      description: 'Expanded browse of academic, cultural, and sports clubs',
      params: { limit: 15 },
      command: 'curl -X GET "http://localhost:8000/api/v1/clubs/directory?limit=15"',
      prompt: 'Browse 15 student clubs on campus'
    },
    {
      id: 'ex-clubs-3',
      label: 'Full Clubs Directory (25 Clubs)',
      badge: '25 Clubs',
      description: 'Comprehensive list of university student life societies',
      params: { limit: 25 },
      command: 'curl -X GET "http://localhost:8000/api/v1/clubs/directory?limit=25"',
      prompt: 'What student organizations can students join?'
    }
  ],
  'medium-student-summary': [
    {
      id: 'ex-bio-1',
      label: 'Student #1 Academic Bio & Advisor',
      badge: 'Student 1',
      description: 'Inspects advisor assignment and degree program for Student #1',
      params: { student_id: 1 },
      command: 'curl -X GET "http://localhost:8000/api/v1/students/1/academic-summary"',
      prompt: 'Who is the academic advisor for student 1?'
    },
    {
      id: 'ex-bio-2',
      label: 'Student #4 Active Enrolled Bio',
      badge: 'Student 4',
      description: 'Checks department, contact info, and program for Student #4',
      params: { student_id: 4 },
      command: 'curl -X GET "http://localhost:8000/api/v1/students/4/academic-summary"',
      prompt: 'Get academic summary and program details for student 4'
    },
    {
      id: 'ex-bio-3',
      label: 'Student #7 Faculty & Department',
      badge: 'Student 7',
      description: 'Audits faculty mentor rank and college department for Student #7',
      params: { student_id: 7 },
      command: 'curl -X GET "http://localhost:8000/api/v1/students/7/academic-summary"',
      prompt: 'Check department and advisor for student 7'
    }
  ],
  'medium-syllabus': [
    {
      id: 'ex-syl-1',
      label: 'Course #1: Calculus In Materials',
      badge: 'Course 1',
      description: 'Inspects required calculus textbooks, ISBNs, and authors for Course #1',
      params: { course_id: 1 },
      command: 'curl -X GET "http://localhost:8000/api/v1/courses/1/syllabus-materials"',
      prompt: 'What textbooks and materials are required for course 1?'
    },
    {
      id: 'ex-syl-2',
      label: 'Course #2: Ethics Seminar Reading',
      badge: 'Course 2',
      description: 'Pulls syllabus specifications and reading list for Course #2',
      params: { course_id: 2 },
      command: 'curl -X GET "http://localhost:8000/api/v1/courses/2/syllabus-materials"',
      prompt: 'Show syllabus and reading list for course 2'
    },
    {
      id: 'ex-syl-3',
      label: 'Course #4: Statistics Software & Text',
      badge: 'Course 4',
      description: 'Retrieves instructional materials and textbooks for Course #4',
      params: { course_id: 4 },
      command: 'curl -X GET "http://localhost:8000/api/v1/courses/4/syllabus-materials"',
      prompt: 'Retrieve required course materials for course 4'
    }
  ],
  'medium-student-finance': [
    {
      id: 'ex-fin-1',
      label: 'Student #1 Invoices & Tuition Ledger',
      badge: 'Student 1',
      description: 'Audits tuition fees, itemized charges, and payment balance for Student #1',
      params: { student_id: 1 },
      command: 'curl -X GET "http://localhost:8000/api/v1/finance/student/1/ledger"',
      prompt: 'What is the outstanding tuition balance for student 1?'
    },
    {
      id: 'ex-fin-2',
      label: 'Student #5 High Outstanding Balance',
      badge: 'Student 5',
      description: 'Examines large unpaid semester invoices and fees for Student #5',
      params: { student_id: 5 },
      command: 'curl -X GET "http://localhost:8000/api/v1/finance/student/5/ledger"',
      prompt: 'Check billing history and unpaid fees for student 5'
    },
    {
      id: 'ex-fin-3',
      label: 'Student #7 Itemized Fee Breakdown',
      badge: 'Student 7',
      description: 'Full reconciliation of invoice line items and recorded payments for Student #7',
      params: { student_id: 7 },
      command: 'curl -X GET "http://localhost:8000/api/v1/finance/student/7/ledger"',
      prompt: 'Show financial ledger and payments for student 7'
    }
  ],
  'medium-library-loans': [
    {
      id: 'ex-loan-1',
      label: 'Card #1: Active Loans & Overdue Check',
      badge: 'Card 1',
      description: 'Audits current book circulation and return dates for Library Card #1',
      params: { card_id: 1 },
      command: 'curl -X GET "http://localhost:8000/api/v1/library/borrower/1/loans"',
      prompt: 'Does library card 1 have any overdue books checked out?'
    },
    {
      id: 'ex-loan-2',
      label: 'Card #2: Circulation History & Due Dates',
      badge: 'Card 2',
      description: 'Inspects borrowed book titles and expiration date for Card #2',
      params: { card_id: 2 },
      command: 'curl -X GET "http://localhost:8000/api/v1/library/borrower/2/loans"',
      prompt: 'Check book loans and return status for card 2'
    },
    {
      id: 'ex-loan-3',
      label: 'Card #4: Borrower Loans in Good Standing',
      badge: 'Card 4',
      description: 'Retrieves active book loans and patron profile for Card #4',
      params: { card_id: 4 },
      command: 'curl -X GET "http://localhost:8000/api/v1/library/borrower/4/loans"',
      prompt: 'View active book loans for borrower card 4'
    }
  ],
  'medium-payment-record': [
    {
      id: 'ex-pay-1',
      label: '$500 Card Payment on Invoice #4',
      badge: '$500 Card',
      description: 'Applies a $500 partial credit card payment against active Invoice #4',
      params: { invoice_id: 4, amount: 500.0, payment_method: 'card' },
      command: 'curl -X POST "http://localhost:8000/api/v1/finance/payments/record" -H "Content-Type: application/json" -d \'{"invoice_id": 4, "amount": 500.0, "payment_method": "card"}\'',
      prompt: 'Pay $500 towards invoice 4 using card'
    },
    {
      id: 'ex-pay-2',
      label: '$1,200 Wire Transfer on Invoice #8',
      badge: '$1,200 Wire',
      description: 'Records an electronic bank wire transfer of $1,200 on Invoice #8',
      params: { invoice_id: 8, amount: 1200.0, payment_method: 'transfer' },
      command: 'curl -X POST "http://localhost:8000/api/v1/finance/payments/record" -H "Content-Type: application/json" -d \'{"invoice_id": 8, "amount": 1200.0, "payment_method": "transfer"}\'',
      prompt: 'Record a $1200 bank transfer payment on invoice 8'
    },
    {
      id: 'ex-pay-3',
      label: '$250 Campus Cash on Invoice #34',
      badge: '$250 Cash',
      description: 'Processes a $250 cash receipt voucher against Invoice #34',
      params: { invoice_id: 34, amount: 250.0, payment_method: 'cash' },
      command: 'curl -X POST "http://localhost:8000/api/v1/finance/payments/record" -H "Content-Type: application/json" -d \'{"invoice_id": 34, "amount": 250.0, "payment_method": "cash"}\'',
      prompt: 'Process a $250 cash payment against invoice 34'
    }
  ],
  'complex-transcript': [
    {
      id: 'ex-tra-1',
      label: 'Student #1: Graduated Honors Transcript',
      badge: 'Student 1',
      description: 'Computes weighted CGPA, grade distribution, and honors standing for Student #1',
      params: { student_id: 1 },
      command: 'curl -X GET "http://localhost:8000/api/v1/students/1/transcript-audit"',
      prompt: 'Audit the full academic transcript and CGPA for student 1'
    },
    {
      id: 'ex-tra-2',
      label: 'Student #4: Multi-Semester Grade Audit',
      badge: 'Student 4',
      description: 'Evaluates semester-by-semester term GPAs and credits earned for Student #4',
      params: { student_id: 4 },
      command: 'curl -X GET "http://localhost:8000/api/v1/students/4/transcript-audit"',
      prompt: 'Check grades, term GPAs, and credits earned for student 4'
    },
    {
      id: 'ex-tra-3',
      label: 'Student #7: Cumulative Standing & Credits',
      badge: 'Student 7',
      description: 'Audits cumulative degree completion percentage and standing for Student #7',
      params: { student_id: 7 },
      command: 'curl -X GET "http://localhost:8000/api/v1/students/7/transcript-audit"',
      prompt: 'Calculate cumulative GPA and academic honors for student 7'
    }
  ],
  'complex-graduation-audit': [
    {
      id: 'ex-grad-1',
      label: 'Student #1: Graduation Clearance (Passed)',
      badge: 'Student 1',
      description: 'Verifies all 4 degree graduation invariants for cleared graduate Student #1',
      params: { student_id: 1 },
      command: 'curl -X GET "http://localhost:8000/api/v1/students/1/graduation-eligibility"',
      prompt: 'Is student 1 eligible to graduate this semester?'
    },
    {
      id: 'ex-grad-2',
      label: 'Student #4: Degree Invariant & Credit Check',
      badge: 'Student 4',
      description: 'Evaluates required credits and minimum 2.50 CGPA threshold for Student #4',
      params: { student_id: 4 },
      command: 'curl -X GET "http://localhost:8000/api/v1/students/4/graduation-eligibility"',
      prompt: 'Run an autonomous degree graduation audit for student 4'
    },
    {
      id: 'ex-grad-3',
      label: 'Student #5: Financial Hold & Action Items',
      badge: 'Student 5',
      description: 'Identifies unpaid tuition hold preventing degree dispatch for Student #5',
      params: { student_id: 5 },
      command: 'curl -X GET "http://localhost:8000/api/v1/students/5/graduation-eligibility"',
      prompt: 'Check if student 5 has any graduation holds or missing credits'
    }
  ],
  'complex-dept-workload': [
    {
      id: 'ex-dept-1',
      label: 'University-Wide Operational Analytics',
      badge: 'All Depts',
      description: 'Ranks academic departments by total student enrollment across active sections',
      params: {},
      command: 'curl -X GET "http://localhost:8000/api/v1/analytics/department-workload"',
      prompt: 'Which academic department has the highest student enrollment workload?'
    },
    {
      id: 'ex-dept-2',
      label: 'Faculty Ratios & Course Offerings',
      badge: 'Faculty Ratios',
      description: 'Calculates student-to-faculty ratios and active sections per department',
      params: {},
      command: 'curl -X GET "http://localhost:8000/api/v1/analytics/department-workload"',
      prompt: 'Show faculty-to-student ratios across all departments'
    },
    {
      id: 'ex-dept-3',
      label: 'Faculty Salary & Load Analysis',
      badge: 'Compensation',
      description: 'Computes average faculty compensation against total enrollment density',
      params: {},
      command: 'curl -X GET "http://localhost:8000/api/v1/analytics/department-workload"',
      prompt: 'Analyze active course sections and faculty salaries by department'
    }
  ],
  'complex-scholarship-matcher': [
    {
      id: 'ex-sch-1',
      label: 'Student #1: High-GPA Merit Matcher',
      badge: 'Student 1',
      description: "Matches Student #1's GPA against high-tier institutional scholarships",
      params: { student_id: 1 },
      command: 'curl -X GET "http://localhost:8000/api/v1/scholarships/eligibility-matcher/1"',
      prompt: 'Match eligible merit and need-based scholarships for student 1'
    },
    {
      id: 'ex-sch-2',
      label: 'Student #4: Active Funding & Opportunities',
      badge: 'Student 4',
      description: 'Surveys active scholarship grants and qualified funding for Student #4',
      params: { student_id: 4 },
      command: 'curl -X GET "http://localhost:8000/api/v1/scholarships/eligibility-matcher/4"',
      prompt: 'Find active awards and matching scholarships for student 4'
    },
    {
      id: 'ex-sch-3',
      label: 'Student #7: Need & GPA Evaluation',
      badge: 'Student 7',
      description: 'Determines qualification for tuition relief and endowed scholarships for Student #7',
      params: { student_id: 7 },
      command: 'curl -X GET "http://localhost:8000/api/v1/scholarships/eligibility-matcher/7"',
      prompt: 'Check scholarship funding eligibility for student 7'
    }
  ],
  'complex-prerequisite-dag': [
    {
      id: 'ex-dag-1',
      label: 'Course #1: Calculus In Prerequisite Chain',
      badge: 'Course 1',
      description: 'Traverses prerequisite requirements tree leading into Course #1',
      params: { course_id: 1 },
      command: 'curl -X GET "http://localhost:8000/api/v1/courses/1/prerequisite-chain"',
      prompt: 'What is the prerequisite dependency DAG for course 1?'
    },
    {
      id: 'ex-dag-2',
      label: 'Course #4: Advanced Statistics DAG',
      badge: 'Course 4',
      description: 'Recursive dependency tree for advanced quantitative statistics Course #4',
      params: { course_id: 4 },
      command: 'curl -X GET "http://localhost:8000/api/v1/courses/4/prerequisite-chain"',
      prompt: 'Traverse the prerequisite sequence needed before enrolling in course 4'
    },
    {
      id: 'ex-dag-3',
      label: 'Course #27: Applied Calculus Multi-Hop',
      badge: 'Course 27',
      description: 'Evaluates foundational math sequence required prior to Course #27',
      params: { course_id: 27 },
      command: 'curl -X GET "http://localhost:8000/api/v1/courses/27/prerequisite-chain"',
      prompt: 'What courses must be completed before taking course 27?'
    }
  ]
};

export default function ApiExplorerModal({ isOpen, onClose, initialCatalog = null, targetEndpointId = null }) {
  const [catalog, setCatalog] = useState(initialCatalog);
  const [loadingCatalog, setLoadingCatalog] = useState(false);
  const [selectedApi, setSelectedApi] = useState(null);
  const [filterComplexity, setFilterComplexity] = useState('All');
  const [searchQuery, setSearchQuery] = useState('');
  
  // Execution state
  const [params, setParams] = useState({});
  const [requestBody, setRequestBody] = useState('');
  const [executing, setExecuting] = useState(false);
  const [responseResult, setResponseResult] = useState(null);
  const [copied, setCopied] = useState(false);
  const [copiedExampleId, setCopiedExampleId] = useState(null);
  const [copiedPromptId, setCopiedPromptId] = useState(null);

  // Schema Drift / Broken API State
  const [activeDriftMode, setActiveDriftMode] = useState('healthy');
  const [customPath, setCustomPath] = useState(null);

  // Close on Escape key
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === 'Escape' && isOpen) {
        onClose();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, onClose]);

  useEffect(() => {
    if (isOpen) {
      if (initialCatalog && initialCatalog.endpoints) {
        setCatalog(initialCatalog);
        if (targetEndpointId) {
          const target = initialCatalog.endpoints.find(e => e.id === targetEndpointId);
          if (target) selectEndpoint(target);
          else if (!selectedApi) selectEndpoint(initialCatalog.endpoints[0]);
        } else if (!selectedApi) {
          selectEndpoint(initialCatalog.endpoints[0]);
        }
      } else {
        loadCatalog();
      }
    }
  }, [isOpen, initialCatalog, targetEndpointId]);

  const loadCatalog = async () => {
    try {
      setLoadingCatalog(true);
      const data = await fetchApiCatalog();
      setCatalog(data);
      if (data.endpoints && data.endpoints.length > 0) {
        if (targetEndpointId) {
          const target = data.endpoints.find(e => e.id === targetEndpointId);
          if (target) selectEndpoint(target);
          else if (!selectedApi) selectEndpoint(data.endpoints[0]);
        } else if (!selectedApi) {
          selectEndpoint(data.endpoints[0]);
        }
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoadingCatalog(false);
    }
  };

  const getDriftOptionsForApi = (endpoint) => {
    if (!endpoint) return [];
    return [
      {
        id: 'healthy',
        label: '🟢 Healthy / Standard Schema (Default)',
        badge: 'Healthy',
        badgeColor: 'bg-emerald-50 text-emerald-700 border-emerald-200',
        description: 'Official API contract v1 with expected parameters and valid types.'
      },
      {
        id: 'param_renamed',
        label: '⚡ Drift 1: Parameter Renamed',
        badge: 'Renamed',
        badgeColor: 'bg-amber-50 text-amber-700 border-amber-200',
        description: 'Simulates field rename (e.g. status -> student_status, search -> keyword, student_id -> candidate_id).'
      },
      {
        id: 'type_mutated',
        label: '⚡ Drift 2: Data Type Mutation (Type Mismatch)',
        badge: 'Type Cast',
        badgeColor: 'bg-purple-50 text-purple-700 border-purple-200',
        description: 'Passes invalid type (e.g. string UUID where integer ID expected), triggering 422 Unprocessable Entity.'
      },
      {
        id: 'nested_wrapped',
        label: '⚡ Drift 3: Nested Object Required',
        badge: 'Nesting',
        badgeColor: 'bg-blue-50 text-blue-700 border-blue-200',
        description: 'Wraps query or body parameters inside a nested filter structure (e.g. filter[param]=val).'
      },
      {
        id: 'missing_required',
        label: '⚡ Drift 4: Missing Mandatory Field',
        badge: 'Missing Field',
        badgeColor: 'bg-red-50 text-red-700 border-red-200',
        description: 'Omits primary required path/query identifier to test endpoint schema validation failure.'
      },
      {
        id: 'route_deprecated',
        label: '⚡ Drift 5: Route Migration (/api/v2 path)',
        badge: 'Route Drift',
        badgeColor: 'bg-rose-50 text-rose-700 border-rose-200',
        description: 'Simulates endpoint path migration drift to /api/v2/, triggering 404 Route Not Found.'
      }
    ];
  };

  const selectEndpoint = (endpoint) => {
    setSelectedApi(endpoint);
    setActiveDriftMode('healthy');
    setCustomPath(null);
    setParams(endpoint.default_params ? { ...endpoint.default_params } : {});
    if (endpoint.method === 'POST') {
      setRequestBody(JSON.stringify(endpoint.default_params, null, 2));
    } else {
      setRequestBody('');
    }
    setResponseResult(null);
  };

  const applyDriftMode = (modeId) => {
    if (!selectedApi) return;
    setActiveDriftMode(modeId);
    setResponseResult(null);

    const baseParams = selectedApi.default_params ? { ...selectedApi.default_params } : {};

    if (modeId === 'healthy') {
      setCustomPath(null);
      setParams(baseParams);
      if (selectedApi.method === 'POST') {
        setRequestBody(JSON.stringify(baseParams, null, 2));
      } else {
        setRequestBody('');
      }
      updateDriftState(selectedApi.id, 'healthy').catch(console.error);
      return;
    }

    let mutatedParams = {};
    let targetPath = null;

    if (modeId === 'param_renamed') {
      const mutated = {};
      Object.entries(baseParams).forEach(([k, v]) => {
        if (k === 'status') mutated['student_status'] = v;
        else if (k === 'search') mutated['keyword'] = v;
        else if (k === 'query') mutated['title_or_author'] = v;
        else if (k === 'student_id') mutated['candidate_id'] = v;
        else if (k === 'course_id') mutated['class_id'] = v;
        else if (k === 'card_id') mutated['borrower_card_no'] = v;
        else if (k === 'invoice_id') mutated['bill_id'] = v;
        else if (k === 'amount') mutated['payment_value'] = v;
        else mutated[`drift_${k}`] = v;
      });
      mutatedParams = mutated;
      setCustomPath(null);
      setParams(mutated);
      if (selectedApi.method === 'POST') {
        setRequestBody(JSON.stringify(mutated, null, 2));
      }
    } else if (modeId === 'type_mutated') {
      const mutated = {};
      Object.entries(baseParams).forEach(([k, v]) => {
        if (typeof v === 'number' || k.endsWith('_id') || k === 'page' || k === 'limit' || k === 'min_credits') {
          mutated[k] = `UUID_ERR_${v}_ALPHA`;
        } else {
          mutated[k] = v;
        }
      });
      mutatedParams = mutated;
      setCustomPath(null);
      setParams(mutated);
      if (selectedApi.method === 'POST') {
        setRequestBody(JSON.stringify(mutated, null, 2));
      }
    } else if (modeId === 'nested_wrapped') {
      const mutated = {};
      Object.entries(baseParams).forEach(([k, v]) => {
        mutated[`filter[${k}]`] = v;
      });
      mutatedParams = mutated;
      setCustomPath(null);
      setParams(mutated);
      if (selectedApi.method === 'POST') {
        setRequestBody(JSON.stringify({ filter: baseParams }, null, 2));
      }
    } else if (modeId === 'missing_required') {
      mutatedParams = {};
      setCustomPath(null);
      setParams({});
      if (selectedApi.method === 'POST') {
        setRequestBody(JSON.stringify({}, null, 2));
      }
    } else if (modeId === 'route_deprecated') {
      mutatedParams = baseParams;
      targetPath = selectedApi.path.replace('/api/v1/', '/api/v2/');
      setParams(baseParams);
      setCustomPath(targetPath);
      if (selectedApi.method === 'POST') {
        setRequestBody(JSON.stringify(baseParams, null, 2));
      }
    }

    // Sync drift state with backend
    updateDriftState(selectedApi.id, modeId, mutatedParams, targetPath).catch(console.error);
  };

  const handleResetToHealthy = () => {
    applyDriftMode('healthy');
  };

  const getEndpointExamples = (endpoint) => {
    if (!endpoint) return [];
    if (endpoint.examples && endpoint.examples.length > 0) return endpoint.examples;
    return DEFAULT_EXAMPLES[endpoint.id] || [];
  };

  const handleRunExample = async (endpoint, example) => {
    selectEndpoint(endpoint);
    setActiveDriftMode('healthy');
    setCustomPath(null);
    const newParams = example.params ? { ...example.params } : {};
    setParams(newParams);
    let bodyData = null;
    if (endpoint.method === 'POST') {
      bodyData = newParams;
      setRequestBody(JSON.stringify(newParams, null, 2));
    } else {
      setRequestBody('');
    }
    setResponseResult(null);
    setExecuting(true);
    try {
      const result = await executeApiEndpoint(endpoint.method, endpoint.path, newParams, bodyData);
      setResponseResult(result);
    } catch (err) {
      setResponseResult({
        ok: false,
        status: 500,
        statusText: 'Client Error',
        latency: 0,
        data: { error: err.message }
      });
    } finally {
      setExecuting(false);
    }
  };

  const handleLoadExample = (example) => {
    setActiveDriftMode('healthy');
    setCustomPath(null);
    const newParams = example.params ? { ...example.params } : {};
    setParams(newParams);
    if (selectedApi?.method === 'POST') {
      setRequestBody(JSON.stringify(newParams, null, 2));
    }
  };

  const copyExampleCurl = (example) => {
    navigator.clipboard.writeText(example.command);
    setCopiedExampleId(example.id);
    setTimeout(() => setCopiedExampleId(null), 2000);
  };

  const copyExamplePrompt = (example) => {
    navigator.clipboard.writeText(example.prompt);
    setCopiedPromptId(example.id);
    setTimeout(() => setCopiedPromptId(null), 2000);
  };

  const handleSend = async (overrideParams = null, overrideBody = null) => {
    if (!selectedApi) return;
    try {
      setExecuting(true);
      setResponseResult(null);
      const activeParams = overrideParams !== null ? overrideParams : params;
      let bodyData = null;
      const rawBody = overrideBody !== null ? overrideBody : requestBody;
      if (selectedApi.method === 'POST' && typeof rawBody === 'string' && rawBody.trim()) {
        try {
          bodyData = JSON.parse(rawBody);
        } catch (e) {
          alert('Invalid JSON in Request Body!');
          setExecuting(false);
          return;
        }
      } else if (selectedApi.method === 'POST' && typeof rawBody === 'object') {
        bodyData = rawBody;
      }
      const activePath = customPath || selectedApi.path;
      const result = await executeApiEndpoint(selectedApi.method, activePath, activeParams, bodyData);
      setResponseResult(result);
    } catch (err) {
      setResponseResult({
        ok: false,
        status: 500,
        statusText: 'Client Error',
        latency: 0,
        data: { error: err.message }
      });
    } finally {
      setExecuting(false);
    }
  };

  const copyResponse = () => {
    if (!responseResult || !responseResult.data) return;
    navigator.clipboard.writeText(JSON.stringify(responseResult.data, null, 2));
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const getResolvedPath = () => {
    if (!selectedApi) return '';
    let p = customPath || selectedApi.path;
    Object.entries(params).forEach(([k, v]) => {
      const placeholder = `{${k}}`;
      if (p.includes(placeholder)) {
        p = p.replace(placeholder, v !== '' && v !== undefined ? v : placeholder);
      }
    });
    return p;
  };

  if (!isOpen) return null;

  const endpoints = catalog?.endpoints || [];
  const filteredEndpoints = endpoints.filter(ep => {
    const matchesComplexity = filterComplexity === 'All' || ep.complexity === filterComplexity;
    const matchesSearch = ep.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
                          ep.path.toLowerCase().includes(searchQuery.toLowerCase()) ||
                          ep.tables.some(t => t.toLowerCase().includes(searchQuery.toLowerCase()));
    return matchesComplexity && matchesSearch;
  });

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-gray-900/50 backdrop-blur-xs p-4 sm:p-6 animate-fadeIn"
      onClick={(e) => { if (e.target === e.currentTarget) onClose(); }}
    >
      <div className="relative w-full h-[94vh] max-w-7xl bg-white border border-gray-200 rounded-xl shadow-2xl flex flex-col overflow-hidden">
        
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-3.5 border-b border-gray-200 bg-white">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-lg bg-orange-50 border border-orange-200 flex items-center justify-center text-[#FF6C37]">
              <Code2 className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2.5">
                <h2 className="text-base font-bold text-gray-900 tracking-tight">University API Catalog & Live Runner</h2>
                <span className="px-2 py-0.5 rounded text-[11px] font-semibold bg-orange-50 text-[#FF6C37] border border-orange-200 font-mono">
                  15 Multi-Table Endpoints
                </span>
                <span className="px-2 py-0.5 rounded text-[11px] font-semibold bg-gray-100 text-gray-700 border border-gray-200">
                  FastAPI Server
                </span>
              </div>
              <p className="text-xs text-gray-500 mt-0.5">
                Ranging from Simple single-table lookups to Complex relational audits across 30 tables
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2.5">
            <a
              href="http://localhost:8000/docs"
              target="_blank"
              rel="noreferrer"
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-semibold bg-white hover:bg-gray-50 text-gray-700 transition-colors border border-gray-300 shadow-2xs cursor-pointer"
            >
              <ExternalLink className="w-3.5 h-3.5 text-[#FF6C37]" />
              Swagger Docs
            </a>

            <button
              onClick={loadCatalog}
              className="p-1.5 rounded-md text-gray-500 hover:text-gray-800 hover:bg-gray-100 transition-colors cursor-pointer"
              title="Refresh Catalog"
            >
              <RefreshCw className={`w-4 h-4 ${loadingCatalog ? 'animate-spin' : ''}`} />
            </button>

            <button
              id="btn-close-api-explorer"
              type="button"
              onClick={onClose}
              className="p-1.5 rounded-md text-gray-400 hover:text-gray-700 hover:bg-gray-100 transition-colors ml-1 cursor-pointer"
              title="Close modal (Esc)"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Main Content Area: Split Sidebar & Runner */}
        <div className="flex flex-1 overflow-hidden">
          
          {/* Left Sidebar: Filter Tabs & Endpoint List */}
          <div className="w-80 border-r border-gray-200 bg-[#F9FAFB] flex flex-col">
            
            {/* Search Box */}
            <div className="p-3 border-b border-gray-200 bg-white">
              <div className="relative">
                <Search className="w-3.5 h-3.5 absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
                <input
                  type="text"
                  placeholder="Search APIs or tables..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="w-full pl-8 pr-3 py-1.5 text-xs bg-white border border-gray-300 rounded-md text-gray-800 placeholder-gray-400 focus:outline-none focus:border-[#FF6C37] focus:ring-1 focus:ring-[#FF6C37]"
                />
              </div>

              {/* Complexity Tabs */}
              <div className="flex items-center gap-1 mt-2">
                {['All', 'Simple', 'Medium', 'Complex'].map(tier => (
                  <button
                    key={tier}
                    onClick={() => setFilterComplexity(tier)}
                    className={`flex-1 py-1 text-[11px] font-semibold rounded-md transition-colors ${
                      filterComplexity === tier
                        ? 'bg-[#FF6C37] text-white shadow-2xs'
                        : 'text-gray-600 hover:bg-gray-100 hover:text-gray-900'
                    }`}
                  >
                    {tier}
                  </button>
                ))}
              </div>
            </div>

            {/* Endpoints List */}
            <div className="flex-1 overflow-y-auto p-2 space-y-1">
              {filteredEndpoints.map(ep => {
                const isSelected = selectedApi?.id === ep.id;
                const epExamples = getEndpointExamples(ep);
                return (
                  <button
                    key={ep.id}
                    onClick={() => selectEndpoint(ep)}
                    className={`w-full text-left p-2.5 rounded-lg border transition-all ${
                      isSelected
                        ? 'bg-orange-50 border-orange-300 shadow-2xs'
                        : 'bg-white hover:bg-gray-100 border-gray-200'
                    }`}
                  >
                    <div className="flex items-center justify-between gap-2 mb-1">
                      <div className="flex items-center gap-1.5">
                        <span className={`px-1.5 py-0.5 rounded text-[10px] font-mono font-bold ${
                          ep.method === 'POST' ? 'bg-orange-100 text-[#FF6C37]' : 'bg-emerald-100 text-emerald-700'
                        }`}>
                          {ep.method}
                        </span>
                        <span className={`text-[10px] font-semibold px-1.5 py-0.2 rounded border ${
                          ep.complexity === 'Simple'
                            ? 'bg-gray-50 text-gray-600 border-gray-200'
                            : ep.complexity === 'Medium'
                            ? 'bg-blue-50 text-blue-700 border-blue-200'
                            : 'bg-purple-50 text-purple-700 border-purple-200'
                        }`}>
                          {ep.complexity}
                        </span>
                      </div>
                      <span className="text-[10px] text-gray-400 font-mono">
                        {ep.tables.length} {ep.tables.length === 1 ? 'tbl' : 'tbls'}
                      </span>
                    </div>

                    <div className="text-xs font-bold text-gray-900 truncate">
                      {ep.name}
                    </div>
                    <div className="text-[11px] text-gray-500 font-mono truncate mt-0.5">
                      {ep.path}
                    </div>

                    {/* 2-3 Example command quick pills right under each API */}
                    {epExamples.length > 0 && (
                      <div className="mt-2 pt-1.5 border-t border-gray-100 flex flex-wrap items-center gap-1">
                        <span className="text-[9px] font-bold text-gray-400 uppercase tracking-wider mr-0.5">
                          Ex:
                        </span>
                        {epExamples.map(ex => (
                          <span
                            key={ex.id}
                            onClick={(e) => {
                              e.stopPropagation();
                              handleRunExample(ep, ex);
                            }}
                            title={`Run example: ${ex.label} (${ex.command})`}
                            className="inline-flex items-center gap-0.5 px-1.5 py-0.5 text-[9px] font-semibold rounded bg-gray-50 hover:bg-[#FF6C37] hover:text-white text-gray-600 transition-all cursor-pointer border border-gray-200 hover:border-[#FF6C37] active:scale-95"
                          >
                            <Zap className="w-2.5 h-2.5 text-amber-500 hover:text-white" />
                            <span>{ex.badge || ex.label.split(':')[0]}</span>
                          </span>
                        ))}
                      </div>
                    )}
                  </button>
                );
              })}
            </div>
          </div>

          {/* Right Runner & Inspector Panel */}
          {selectedApi ? (
            <div className="flex-1 flex flex-col bg-white overflow-hidden">
              
              {/* URL & Send Bar with Schema Drift / Break API Dropdown and Reset Button */}
              <div className="p-4 border-b border-gray-200 bg-gray-50/50 flex flex-col gap-3">
                <div className="flex flex-wrap items-center gap-2.5">
                  <span className={`px-2.5 py-1.5 rounded-md text-xs font-mono font-extrabold shadow-2xs shrink-0 ${
                    selectedApi.method === 'POST'
                      ? 'bg-orange-100 text-[#FF6C37] border border-orange-200'
                      : 'bg-emerald-100 text-emerald-700 border border-emerald-200'
                  }`}>
                    {selectedApi.method}
                  </span>

                  {/* Schema Drift Selector Dropdown (Right beside GET tag) */}
                  <div className="flex items-center gap-1.5 shrink-0">
                    <div className="relative">
                      <select
                        id="select-api-drift-version"
                        value={activeDriftMode}
                        onChange={(e) => applyDriftMode(e.target.value)}
                        className={`pl-2.5 pr-8 py-1.5 text-xs font-semibold rounded-md border shadow-2xs focus:outline-none transition-all cursor-pointer ${
                          activeDriftMode === 'healthy'
                            ? 'bg-white text-gray-800 border-gray-300 hover:border-gray-400'
                            : 'bg-amber-50 text-amber-900 border-amber-400 ring-1 ring-amber-400 font-bold'
                        }`}
                        title="Simulate Schema Drift / Break API Contract"
                      >
                        {getDriftOptionsForApi(selectedApi).map(opt => (
                          <option key={opt.id} value={opt.id}>
                            {opt.label}
                          </option>
                        ))}
                      </select>
                    </div>

                    {/* Reset Button (Reverts to healthy original query) */}
                    <button
                      id="btn-reset-api-schema"
                      type="button"
                      onClick={handleResetToHealthy}
                      disabled={activeDriftMode === 'healthy'}
                      className="flex items-center gap-1 px-2.5 py-1.5 text-xs font-semibold rounded-md border border-gray-300 bg-white hover:bg-gray-100 active:bg-gray-200 text-gray-700 disabled:opacity-40 disabled:cursor-not-allowed shadow-2xs transition-colors shrink-0"
                      title="Reset and auto-select standard healthy query"
                    >
                      <RotateCcw className="w-3.5 h-3.5 text-gray-500" />
                      <span>Reset</span>
                    </button>
                  </div>

                  {/* URL Display Bar */}
                  <div className="flex-1 min-w-[220px] flex items-center px-3 py-1.5 bg-white border border-gray-300 rounded-md font-mono text-xs text-gray-800 shadow-inner overflow-hidden">
                    <span className="text-gray-400 mr-1 shrink-0">http://localhost:8000</span>
                    <span className={`font-semibold truncate ${activeDriftMode !== 'healthy' ? 'text-amber-700 underline decoration-amber-400' : 'text-gray-900'}`}>
                      {getResolvedPath()}
                    </span>
                  </div>

                  <button
                    onClick={handleSend}
                    disabled={executing}
                    className="flex items-center gap-2 px-5 py-2 rounded-md text-xs font-bold bg-[#FF6C37] hover:bg-[#E85B27] active:bg-[#D44C1A] text-white shadow-sm transition-all disabled:opacity-50 shrink-0"
                  >
                    <Send className={`w-3.5 h-3.5 ${executing ? 'animate-spin' : ''}`} />
                    {executing ? 'Executing...' : 'Send Request'}
                  </button>
                </div>

                {/* API Metadata Header */}
                <div className="flex flex-wrap items-center justify-between gap-2 pt-1 text-xs">
                  <div>
                    <h3 className="text-sm font-bold text-gray-900">{selectedApi.name}</h3>
                    <p className="text-xs text-gray-600 mt-0.5">{selectedApi.description}</p>
                  </div>
                  <div className="flex items-center gap-1.5">
                    <span className="text-[11px] text-gray-500 font-medium">Tables Used:</span>
                    {selectedApi.tables.map(tbl => (
                      <span key={tbl} className="px-2 py-0.5 bg-white border border-gray-200 rounded text-[10px] font-mono text-gray-700">
                        {tbl}
                      </span>
                    ))}
                  </div>
                </div>
              </div>

              {/* Lower Section: Parameters + Live Response View */}
              <div className="flex-1 grid grid-cols-1 lg:grid-cols-2 overflow-hidden divide-y lg:divide-y-0 lg:divide-x divide-gray-200">
                
                {/* Parameters & Request Configuration */}
                <div className="flex flex-col p-4 overflow-y-auto space-y-4">
                  
                  {/* Schema Drift Active Alert Banner */}
                  {activeDriftMode !== 'healthy' && (
                    <div className="p-3 rounded-lg bg-amber-50 border border-amber-300 text-xs flex items-start justify-between gap-2 text-amber-900 animate-fadeIn">
                      <div className="flex items-start gap-2">
                        <AlertTriangle className="w-4 h-4 text-amber-600 shrink-0 mt-0.5" />
                        <div>
                          <div className="font-bold flex items-center gap-1.5">
                            <span>Schema Drift Injected:</span>
                            <span className="font-mono text-[10px] px-1.5 py-0.2 bg-amber-200 text-amber-900 rounded font-bold">
                              {activeDriftMode.toUpperCase()}
                            </span>
                          </div>
                          <p className="text-[11px] text-amber-800 mt-0.5">
                            {getDriftOptionsForApi(selectedApi).find(o => o.id === activeDriftMode)?.description}
                          </p>
                        </div>
                      </div>
                      <button
                        onClick={handleResetToHealthy}
                        className="px-2 py-0.5 bg-white hover:bg-amber-100 border border-amber-300 text-amber-900 rounded text-[10px] font-semibold shrink-0"
                      >
                        Reset Schema
                      </button>
                    </div>
                  )}

                  {/* Showcase Example Commands Section */}
                  <div className="p-3.5 bg-gradient-to-r from-orange-50/80 via-white to-amber-50/40 border border-orange-200 rounded-xl space-y-2.5 shadow-2xs">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <div className="w-5 h-5 rounded-md bg-[#FF6C37] text-white flex items-center justify-center shadow-xs">
                          <Sparkles className="w-3 h-3" />
                        </div>
                        <div>
                          <h4 className="text-xs font-bold text-gray-900 flex items-center gap-1.5">
                            <span>Showcase Example Commands</span>
                            <span className="px-1.5 py-0.2 rounded text-[10px] font-bold bg-orange-100 text-[#FF6C37] border border-orange-200 font-mono">
                              {getEndpointExamples(selectedApi).length} Examples
                            </span>
                          </h4>
                          <p className="text-[11px] text-gray-500">
                            Click any example below to auto-fill parameters and execute live against SQLite
                          </p>
                        </div>
                      </div>
                    </div>

                    <div className="grid grid-cols-1 gap-2 pt-0.5">
                      {getEndpointExamples(selectedApi).map((ex, idx) => {
                        const isParamActive = JSON.stringify(ex.params) === JSON.stringify(params);
                        const isCurlCopied = copiedExampleId === ex.id;
                        const isPromptCopied = copiedPromptId === ex.id;

                        return (
                          <div
                            key={ex.id}
                            className={`p-2.5 rounded-lg border transition-all text-xs ${
                              isParamActive
                                ? 'bg-orange-50/90 border-[#FF6C37] shadow-xs ring-1 ring-[#FF6C37]/30'
                                : 'bg-white hover:bg-gray-50/80 border-gray-200'
                            }`}
                          >
                            <div className="flex items-center justify-between gap-2 mb-1">
                              <div className="flex items-center gap-1.5 min-w-0">
                                <span className="px-1.5 py-0.5 rounded text-[10px] font-mono font-bold bg-gray-100 text-gray-700 border border-gray-200 shrink-0">
                                  Ex {idx + 1}
                                </span>
                                <span className="font-bold text-gray-900 truncate">
                                  {ex.label}
                                </span>
                                {isParamActive && (
                                  <span className="px-1.5 py-0.2 rounded text-[9px] font-bold bg-emerald-100 text-emerald-800 border border-emerald-200 shrink-0">
                                    Active
                                  </span>
                                )}
                              </div>

                              <div className="flex items-center gap-1 shrink-0">
                                <button
                                  type="button"
                                  onClick={() => handleRunExample(selectedApi, ex)}
                                  disabled={executing}
                                  className="flex items-center gap-1 px-2.5 py-1 text-[11px] font-bold bg-[#FF6C37] hover:bg-[#E85B27] active:bg-[#D44C1A] text-white rounded shadow-2xs transition-all cursor-pointer disabled:opacity-50"
                                  title="Auto-fill parameters and execute immediately against SQLite"
                                >
                                  <Play className="w-3 h-3 fill-current" />
                                  <span>Run</span>
                                </button>

                                <button
                                  type="button"
                                  onClick={() => handleLoadExample(ex)}
                                  className="flex items-center gap-1 px-2 py-1 text-[10px] font-semibold bg-white hover:bg-gray-100 active:bg-gray-200 text-gray-700 border border-gray-300 rounded shadow-2xs transition-colors cursor-pointer"
                                  title="Load parameters into form without immediate execution"
                                >
                                  <span>Fill</span>
                                </button>

                                <button
                                  type="button"
                                  onClick={() => copyExampleCurl(ex)}
                                  className="flex items-center gap-1 px-2 py-1 text-[10px] font-semibold bg-white hover:bg-gray-100 active:bg-gray-200 text-gray-700 border border-gray-300 rounded shadow-2xs transition-colors cursor-pointer"
                                  title="Copy cURL command to clipboard"
                                >
                                  {isCurlCopied ? <Check className="w-3 h-3 text-emerald-600" /> : <Terminal className="w-3 h-3 text-gray-500" />}
                                  <span>{isCurlCopied ? 'Copied' : 'cURL'}</span>
                                </button>

                                <button
                                  type="button"
                                  onClick={() => copyExamplePrompt(ex)}
                                  className="flex items-center gap-1 px-2 py-1 text-[10px] font-semibold bg-white hover:bg-gray-100 active:bg-gray-200 text-gray-700 border border-gray-300 rounded shadow-2xs transition-colors cursor-pointer"
                                  title="Copy Chatbot plain English prompt"
                                >
                                  {isPromptCopied ? <Check className="w-3 h-3 text-emerald-600" /> : <MessageSquare className="w-3 h-3 text-[#FF6C37]" />}
                                  <span>{isPromptCopied ? 'Copied' : 'Prompt'}</span>
                                </button>
                              </div>
                            </div>

                            <p className="text-[11px] text-gray-600 mb-1.5">
                              {ex.description}
                            </p>

                            <div className="bg-gray-900 rounded px-2.5 py-1.5 font-mono text-[11px] text-emerald-400 flex items-center justify-between overflow-x-auto shadow-inner">
                              <span className="truncate pr-2">{ex.command}</span>
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  </div>

                  <div className="flex items-center justify-between pb-2 border-b border-gray-100">
                    <h4 className="text-xs font-bold text-gray-900 uppercase tracking-wider">
                      Request Parameters
                    </h4>
                    <span className="text-[11px] text-gray-500 font-mono">
                      {Object.keys(params).length} parameter(s)
                    </span>
                  </div>

                  {selectedApi.method === 'GET' && Object.keys(params).length > 0 ? (
                    <div className="space-y-3">
                      {Object.entries(params).map(([key, val]) => (
                        <div key={key}>
                          <label className="block text-[11px] font-mono font-semibold text-gray-700 mb-1">
                            {key} {selectedApi.path.includes(`{${key}}`) && <span className="text-[#FF6C37]">*Path</span>}
                          </label>
                          <input
                            type="text"
                            value={val ?? ''}
                            onChange={(e) => setParams({ ...params, [key]: e.target.value })}
                            className="w-full px-3 py-1.5 text-xs bg-white border border-gray-300 rounded-md text-gray-800 font-mono focus:outline-none focus:border-[#FF6C37] focus:ring-1 focus:ring-[#FF6C37]"
                          />
                        </div>
                      ))}
                    </div>
                  ) : selectedApi.method === 'POST' ? (
                    <div className="flex-1 flex flex-col">
                      <label className="block text-[11px] font-mono font-semibold text-gray-700 mb-1">
                        JSON Request Body:
                      </label>
                      <textarea
                        rows={8}
                        value={requestBody}
                        onChange={(e) => setRequestBody(e.target.value)}
                        className="w-full p-3 text-xs bg-gray-50 border border-gray-300 rounded-md font-mono text-gray-800 focus:outline-none focus:border-[#FF6C37] focus:bg-white resize-none"
                      />
                    </div>
                  ) : (
                    <div className="p-4 rounded-md bg-gray-50 border border-gray-200 text-xs text-gray-500 text-center">
                      This endpoint requires no parameters. Click "Send Request" to execute.
                    </div>
                  )}

                  <div className="p-3 bg-orange-50/70 border border-orange-200 rounded-lg text-xs text-orange-950">
                    <span className="font-semibold text-[#FF6C37] block mb-0.5">Relational Intelligence:</span>
                    This endpoint queries SQLite 3 with full integrity and returns live calculated fields across the database.
                  </div>
                </div>

                {/* Live Response Panel */}
                <div className="flex flex-col bg-gray-50/30 overflow-hidden">
                  
                  {/* Response Status Bar */}
                  <div className="p-3 border-b border-gray-200 bg-white flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <h4 className="text-xs font-bold text-gray-900 uppercase tracking-wider">Response</h4>
                      {responseResult && (
                        <div className="flex items-center gap-2">
                          <span className={`px-2 py-0.5 rounded text-[11px] font-mono font-bold ${
                            responseResult.ok
                              ? 'bg-emerald-100 text-emerald-700 border border-emerald-200'
                              : 'bg-red-100 text-red-700 border border-red-200'
                          }`}>
                            {responseResult.status} {responseResult.statusText}
                          </span>
                          <span className="flex items-center gap-1 text-[11px] text-gray-500 font-mono">
                            <Clock className="w-3 h-3" />
                            {responseResult.latency} ms
                          </span>
                        </div>
                      )}
                    </div>

                    {responseResult?.data && (
                      <button
                        onClick={copyResponse}
                        className="flex items-center gap-1 px-2.5 py-1 text-[11px] font-medium text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded border border-gray-200 transition-colors"
                      >
                        <Copy className="w-3 h-3 text-[#FF6C37]" />
                        {copied ? 'Copied!' : 'Copy JSON'}
                      </button>
                    )}
                  </div>

                  {/* Response Body Viewer */}
                  <div className="flex-1 p-3 overflow-auto bg-gray-900 text-emerald-400 font-mono text-xs">
                    {executing ? (
                      <div className="flex items-center justify-center h-full text-gray-400 gap-2">
                        <RefreshCw className="w-4 h-4 animate-spin text-[#FF6C37]" />
                        Executing query against SQLite database...
                      </div>
                    ) : responseResult ? (
                      <pre className="whitespace-pre-wrap">
                        {JSON.stringify(responseResult.data, null, 2)}
                      </pre>
                    ) : (
                      <div className="flex flex-col items-center justify-center h-full text-gray-500">
                        <Send className="w-6 h-6 text-gray-600 mb-2" />
                        <p>Click "Send Request" to execute this API live.</p>
                      </div>
                    )}
                  </div>

                </div>

              </div>
            </div>
          ) : (
            <div className="flex-1 flex items-center justify-center text-gray-400 text-xs">
              Select an API from the catalog list on the left
            </div>
          )}

        </div>

      </div>
    </div>
  );
}
