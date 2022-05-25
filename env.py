import ast
from kubernetes.client import CustomObjectsApi, V1PodSpec, BatchV1Api
from Genetic import *
from kubernetes import client, config, watch
from kubernetes.client import V1JobList, V1Job

# ##### Give them a random string as scylduer, all of them on pending ,
# ### and then with every pod name change it's spec
#


config.load_kube_config()  ## From control panel

# from DQN_skeleton import *
import time
import random

#### we need to add the BUFFER Replay Memory
class Task(object):
    """
    information of each task
    parent, child base on dependency
    jobID, index, CPU, RAM, disk extracted from user data
    status indicates the current status of the task
    """

    def __init__(self, jobID, index, CPU, RAM, disk, status):
        import random
        import time
        self.jobID = jobID
        self.CPU = CPU
        self.status = status  # -1: rejected, 0: finished, 1: ready, 2: running


class DAG(object):
    """
    Transform job queue to task ready queue
    """

    def __init__(self, num_task):
        self.num_task = num_task
        self.job = []
        self.task = []

    def getting_tasks(self):
        """
        Getting the current pending tasks from kubernetes
        :return:
        """
        pass

    def readfile(self):
        """
        Read the input job file
        All task are initialized to ready status
        """
        num_task = 0
        with open(self.fname, 'r') as f:
            task = []
            for line in f:
                if line[0] == 'J':
                    if len(task) != 0:
                        self.job.append(task)
                        task = []
                else:
                    info = list(line.strip(' ').split())
                    task.append(Task(info[1], info[2], float(info[4]), float(info[5]), info[6], 1))
                    num_task += 1
                if num_task == self.num_task:
                    break
            if len(task) != 0:
                self.job.append(task)

    def rejTask(self, task):
        """
        If one task is rejected
        Then all tasks that depended on this task will be rejected
        """
        task.status = -1
        for c in task.child:
            self.rejTask(c)

    def updateStatus(self, task):
        """
            might need it later for updating tasks status for once scheduled
        """
        pass

    def initTask(self):
        """
        run readfile and buildDAG functions
        """
        self.readfile()
        self.buildDAG()

    def taskQueue(self):
        """
        Build the task ready queue
        Just put the one whose status is 1
        and whose parent are all finished
        """
        for job in self.job:
            #             num_task = len(job)
            #             while num_task > 0:
            for task in job:
                if task.status == 1 and self.hasParent(task) == False:
                    self.task.append(task)

    #                     task.status = 0
    #                     self.updateStatus(task)
    #                     num_task -= 1
    #         for t in self.task:
    #             t.status = 1
    #         print(len(self.task), "requests")
    #         self.printTask()

    def printTask(self):
        """
        Print tasks which are in task queue info
        """
        for j in self.task:
            print(j.jobID, ",", j.index, ",", j.status, ",", len(j.parent))


class environment(object):
    """docstring for environment
    the environment of RP/TS processor
    read the task from txt file
    calculate the Reward Function
    interface with DQN and baseline
    """

    def __init__(self, scale, fname, num_task, num_server):
        """
            initing our envi with our present and avaibles nodes with their cores, CPUS, memory( will see )
        """

        self.task = []
        self.dag = DAG(self.fname, num_task) ## will se if we keep this once
        self.VMNum = 5 ### len avaibles nodes
        self.rej = 0
        self.num_task = num_task

        self.FarmResources = []
        self.severs = [[1, 1] for _ in range(self.severNum)]
        self.VMtask = []
        self.totalcost = 0

    #         print("Total Number of tasks: {0}".format(num_task))

    def init_severs(self, severNum):
        """
        Set the initial values for each VMs

        """

        VM = [[[1.0 / self.VMNum, 1.0 / self.VMNum] for _ in range(self.VMNum)] for _ in range(severNum)]
        #         VM = [[[1.0 , 1.0 ] for _ in range(self.VMNum)] for _ in range(severNum)]
        self.VMtask.append([[[] for _ in range(self.VMNum)] for _ in range(severNum)])
        return VM

    def generateQueue(self):
        """
        will see also
        """
        self.dag.taskQueue()
        self.task = self.dag.task

    def setFarm(self): #### DROP this
        """
        Randomly set the servers to each farm
        Each farm has at least 1 server and at most 2*m/n-1 servers
        Initial power usage for each servers and each farm
        """
        import random
        self.farmOri = []
        m = self.severNum
        n = self.farmNum
        f = int(self.severNum / self.farmNum)
        for _ in range(self.farmNum):
            #             f = random.randint(0,int(2*m/n))
            #             f = random.randint(1, int(2 * m / n))
            self.remainFarm.append(self.init_severs(f))
            self.FarmResources.append([f, f])
            self.farmOri.append(f)
            m -= f
            n -= 1

        self.farmOri.append(m)
        self.pwrPre = [0] * self.severNum  # power usage pre sever
        self.pwrPFarm = [0] * self.farmNum  # power usage per farm

    def elecPrice(self, t, pwr): # drop this also we do not need this so far
        """
        The energy cost on time t
        threshold get from "Impact of dynamic energy pricing schemes on a novel multi-user home energy management system"
        price get from "Optimal residential load
        control with price prediction in real-time electricity pricing environments"



        """
        threshold = 1.5
        if pwr < threshold:
            p = 5.91  # dynamic price
        else:
            p = 8.27
        return pwr * p

    def getPwr(self, r, c): ## we need to change this MAYBEE to our resrource use in nodes
        """
        Implement the energy consumption model
        r: the remain CPU
        c: the total(unit) CPU
        The parameters' value get from "An energy and deadline aware resource provisioning, scheduling and optimization framework for cloud systems"
        """
        # eq.2
        if r < c:
            pwrS = 1
        else:
            pwrS = 0
        alpha = 0.5  # alpha
        beta = 10  # beta
        Ur = (c - r) / c  # eq.1
        if Ur < 0.7:
            pwrDy = alpha * Ur
        else:
            pwrDy = 0.7 * alpha + (Ur - 0.7) ** 2 * beta
        return pwrDy + pwrS

    def rewardFcn1(self):
        """
        Implement the reward function for each farm
        For stage 1: choose the farm
        """
        # eq.5
        pwrCFarm = []
        for i in range(self.farmNum):
            pwrc = self.getPwr(self.FarmResources[i][0], self.farmOri[i])
            pwrCFarm.append(pwrc)
        pwr = sum(pwrCFarm) - sum(self.pwrPFarm)
        self.pwrPFarm = pwrCFarm
        return self.elecPrice(1, pwr)


    def rewardFcn2(self):
        """
        Implement the reward function for each server
        For stage 2: choose the server
        """
        # eq.6
        pwrCur = []
        for f in self.remainFarm:
            for s in f:
                sremain = 0
                for v in s:
                    sremain += v[0]
                #                 print(sremain)
                pwrc = self.getPwr(sremain, 1.0)
                if pwrc < 0:
                    print("here", sremain)
                pwrCur.append(pwrc)
        #                 print("pwrc", pwrc)
        pwr = sum(pwrCur) - sum(self.pwrPre)
        self.totalcost += sum(pwrCur)
        #         print("sum(pwrCur)", sum(pwrCur), "sum(self.pwrPre)", sum(self.pwrPre))
        self.pwrPre = pwrCur
        #         print("pwr",pwr)
        #         print("r2", self.elecPrice(1,pwr))
        return self.elecPrice(1, pwr)

    def release(self):
        """
        Randomly release resources from each VM
        And set the corresponding task as finished
        """
        ranFarm = random.randint(0, self.farmNum - 1)
        ranSer = random.randint(0, self.farmOri[ranFarm] - 1)
        ranVM = random.randint(0, self.VMNum - 1)
        if self.VMtask[ranFarm][ranSer][ranVM]:
            random.shuffle(self.VMtask[ranFarm][ranSer][ranVM])
            t = self.VMtask[ranFarm][ranSer][ranVM].pop()
            t.status = 0
            self.remainFarm[ranFarm][ranSer][ranVM][0] += float(t.CPU)
            self.remainFarm[ranFarm][ranSer][ranVM][1] += float(t.RAM)

    def releaseByTime(self, farm_i, server_i, vm_j):
        curtime = time.time()
        for t in self.VMtask[farm_i][server_i][vm_j]:
            if t.endtime < curtime:
                t.status = 0
                self.remainFarm[farm_i][server_i][vm_j][0] += float(t.CPU)
                self.remainFarm[farm_i][server_i][vm_j][1] += float(t.RAM)
                self.FarmResources[farm_i][0] += float(t.CPU)
                self.FarmResources[farm_i][1] += float(t.RAM)
                self.VMtask[farm_i][server_i][vm_j].remove(t)

    def training(self):
        """
        Run the DQN/baseline in the RP/TS processor environment
        Read the task file by readfile()
        Set the variables
        Pass tasks to agents in real time
        Get the corresponding reward value
        Reject task when R_cpu ≥ C_cpu or R_ram < C_ram
        """
        # send one tesk to dqn and calculate reward
        self.dag.initTask()
        self.generateQueue()
        time_start = time.time()
        print(self.farmNum, end=' ')
        print(self.severNum, end=' ')
        print(self.num_task, end=' ')
        print('staring training')
        self.trainDQN_v1()
        time_end = time.time()
        timecost = round(time_end - time_start, 3)
        print(timecost, end=' ')
        print(round(self.totalcost, 3), end=' ')
        print()


    def checkRej(self, farm_i, server_i, vm_j, task): ### we prob don't need this
        """
        Check whether this task should be rejected in ith sever, jth VM
        Reject task when current time + task's runtime > task's ddl
        """
        import time
        if task.CPU > 1 / self.VMNum or task.RAM > 1 / self.VMNum:
            self.rej += 1
            return -1
        remain_cpu = self.remainFarm[farm_i][server_i][vm_j][0] - float(task.CPU)
        remain_ram = self.remainFarm[farm_i][server_i][vm_j][1] - float(task.RAM)
        curtime = time.time()
        if curtime + task.runtime <= task.ddl:
            if remain_cpu >= 0 and remain_ram >= 0:
                return 0  # do not reject
            else:
                return 1  # reject temporarily because cpu or ram
        else:
            self.rej += 1
            return -1  # reject because ddl

    def UpdateServerState(self, tempServerFarm, tempSever, vm_numb, task): ## same don't think we do
        self.remainFarm[tempServerFarm][tempSever][vm_numb][0] -= float(task.CPU)
        self.remainFarm[tempServerFarm][tempSever][vm_numb][1] -= float(task.RAM)
        self.FarmResources[tempServerFarm][0] -= float(task.CPU)
        self.FarmResources[tempServerFarm][1] -= float(task.RAM)
        return self.custom_reshape(self.remainFarm)

    def custom_reshape(self, a):
        result = []
        for farNum in a:
            for serNum in farNum:
                result.append(serNum)
        c = np.array(result)
        d = c.reshape(2 * self.VMNum * self.severNum)
        return d

    """
    # initialize the DQN stage 2 and environment for it, DQN(intial_state, Num_actions)
        # state = state of all VMs in a server farm
        # numb_actions = num of VMs in that sever
    # initiate DQN stage 1 and env for it, state will be only server remainFarm
            # reconstruct self.remainFarm with 3 Dimensional array with heiracrchy as
            # farmNumb->serverNumb->vmNumb[cpu, memory, local] eg. [[[0.002, 0.005, 0.003], [],],[],]
            # convert the remainFarm into 1D array
      # fun to upadate server state after the task has been assigned to server farm
      
    
     """
## dropp the two stages
    def trainDQN_v1(self):
        rej = 0
        self.setFarm()
        energy = 0
        input_stage2 = input_stage1 = self.custom_reshape(self.remainFarm)
        Agent_stage1 = Agent(lr=0.0001, input_dims=len(input_stage1),
                             n_actions=self.farmNum)
        stage1_current_state = input_stage1
        # input_stage2 = np.array(self.remainFarm[0]).reshape(2*self.VMNum*int(self.severNum/self.farmNum))
        Agent_stage2 = Agent(lr=0.0001, input_dims=len(input_stage2),
                             n_actions=int(self.severNum / self.farmNum))
        stage2_current_state = input_stage2
        acc = 0
        while len(self.task) != 0:
            print("len tasks ", len(self.task))
            while len(self.task) != 0:
                for t in self.task:
                    if t.status == -1:  # rejected
                        self.dag.updateStatus(t)
                        self.task.remove(t)
                        print("rejecint ", t)
                    elif t.status == 1:  # ready
                        f = stage1_action = Agent_stage1.processDQN_stage1(stage1_current_state)
                        s = stage2_action = Agent_stage2.processDQN_stage2(stage2_current_state)
                        vm = random.randint(0, self.VMNum - 1)
                        self.releaseByTime(f, s, vm)  # release by time
                        rej = self.checkRej(f, s, vm, t)
                        if rej == -1:  # rejected due to ddl
                            t.status = -1
                        # if not reject:
                        elif rej == 0:
                            ## this takes each task one by one,
                            ## what we need to analyse all tasks first and than chose the action
                            # we have to change a loooot
                            print('starting training on ', t)
                            t.endtime = time.time() + t.runtime
                            stage1_next_state = stage2_next_state = self.UpdateServerState(f, s, vm, t)
                            #                             print(self.remainFarm)
                            reward_stage2 = self.rewardFcn2()
                            energy += reward_stage2
                            Agent_stage2.learn(stage2_current_state, stage2_action, reward_stage2, stage2_next_state)
                            stage2_current_state = stage2_next_state
                            reward_stage1 = self.rewardFcn1()
                            ### this is where we put our  reward funcrion soo that once it has chosen and lucnched sced
                            ## we get metrics and compare them
                            Agent_stage1.learn(stage1_current_state, stage1_action, reward_stage1, stage1_next_state)
                            stage1_current_state = stage1_next_state
                            self.VMtask[f][s][vm].append(t)
                            t.status = 2
                            #                             self.dag.updateStatus(t)
                            self.task.remove(t)
                            acc += 1
            #                         else:
            #                             t.status = -1
            #                             rej += 1
            self.generateQueue()
        # print("total number of tasks: {0}, rejected tasks: {1}".format(len(self.task), rej))
        print(round(1 - acc / self.num_task, 3), end=' ')


p1 = environment('small', 'in.txt', 5000, 300)
p1.training()
