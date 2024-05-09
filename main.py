from typing import Union,List
import math
from fastapi import FastAPI
from pydantic import BaseModel,validator
from typing import Optional, Any
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.middleware.cors import CORSMiddleware
from fastapi.encoders import jsonable_encoder
import jwt
from dotenv import load_dotenv
import uvicorn
import os
# Load environment variables from .env file
load_dotenv()

# Define user credentials
users = {
    os.getenv("USER1_USERNAME"): os.getenv("USER1_PASSWORD"),
    os.getenv("USER2_USERNAME"): os.getenv("USER2_PASSWORD"),
    os.getenv("USER3_USERNAME"): os.getenv("USER3_PASSWORD"),
    os.getenv("USER4_USERNAME"): os.getenv("USER4_PASSWORD"),
}

app = FastAPI()
payment_rate=0.9
# teaching_cost=100000
# trial_teaching_cost=
ck_cost=150000
mep_base_ratio=1.00
mep_inc_ratio=0.1
others_inc_ratio=0.05
mep_and_others_inc_threshold=50
mep_base_cost=1500000
royalty_ratio=[0.1,0.15,0.2]
drop_rate=0.03
fixed_asset_inc_ratio=0.2
fixed_asset_inc_threshold=100

SECERT_KEY = "YOUR_FAST_API_SECRET_KEY"
ALGORITHM ="HS256"
ACCESS_TOKEN_EXPIRES_MINUTES = 800

test_user = {
   "username": "timedoor",
    "password": "admintimedoor123",

}

app = FastAPI()

# origins = {
#     "http://localhost",
#     "http://localhost:5173"
# }
# uvicorn main:app  --reload --host 0.0.0.0 --port 8000

# app.add_middleware(
#    CORSMiddleware,
#     allow_origins = origins,
#     allow_credentials =True,
#     allow_methods = ["*"],
#     allow_headers= ["*"],
# )

origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class InitRequest(BaseModel):
    new_st: int
    max_st:int
    drop_rate: float
    class_price:float
    ckit_price:float
    ruko_rent: float
    mep: float
    off_facility: float
    t_material: float
    off_renov: float
    teaching_cost: float
    ck_cost: float
    admin_cost: float
    marketing_cost: float
    mep_monthly:float
    license_fee:float
    # is_vp:bool
    investment_type:str
    others_cost:float
    

class MonthlyCOG(BaseModel):
    class_sess_num:int = 0
    total_reg_teach_cost:float = 0
    total_trial_teach_cost:float=0
    total_ck_cost:float = 0
    mep_cost:float = 0
    royalty_cost:float = 0
    total_cog:float=0

class MonthlySGA(BaseModel):
    admin_cost:float = 0
    bm_cost:float = 0
    marketing_cost:float = 0
    others_cost:float=0
    fixed_asset_cost:float=0
    total_sga:float=0
    ruko_rent:float=0

class VPSGA(BaseModel):
    ruko_rent:float=0
    additional_rennovation:float=0
    total_vp_sga:float=0
    # @validator("total_sga", always=True)
    # def set_if_empty(cls, v: float, values: dict[str, Any]) -> float:
    #     if v == 0:
    #         return values["admin_cost"] + values["marketing_cost"] + values["bm_cost"] + values["others_cost"]
    #     return v

class MonthlyIncomeProfit(BaseModel):
    gross_profit:float=0
    ord_income:float=0
    cum_profit:float=0
    partner_profit:float=0
    partner_cum_profit:float=0

class MonthlySales(BaseModel):
    month:int
    new_st: int
    active_st:int
    drop_st:int
    c_price:float
    ckit_price:float
    c_sales:float
    ckit_sales:float
    total_sales: float = 0
    cog: MonthlyCOG = MonthlyCOG()
    sga: MonthlySGA = MonthlySGA()
    vp_sga:VPSGA = VPSGA()
    profit:MonthlyIncomeProfit=MonthlyIncomeProfit()

    @validator("total_sales", always=True)
    def set_if_empty_ts(cls, v: float, values: dict[str, Any]) -> float:
        if v == 0:
            return values["c_sales"] + values["ckit_sales"]
        return values["c_sales"] + values["ckit_sales"]
    
    # @validator("cog", always=True)
    # def set_if_empty_cog(cls, v: MonthlyCOG, values: dict[str, Any]) -> MonthlyCOG:
    #     v.class_sess_num=math.ceil(values["active_st"]/4)*4
    #     v.total_reg_teach_cost= v.class_sess_num*teaching_cost
    #     v.total_ck_cost=values["new_st"]*ck_cost
    #     ratio = mep_base_ratio + ((values["active_st"] - 1) // mep_and_others_inc_threshold) * mep_inc_ratio
    #     v.mep_cost = mep_base_cost*ratio
    #     v.royalty_cost = values["total_sales"]*royalty_ratio[0]
    #     v.total_cog = v.total_reg_teach_cost + v.total_ck_cost + v.mep_cost + v.royalty_cost
    #     return v

    # @validator("profit",always=True)
    # def set_if_empty_profit(cls, v: MonthlyIncomeProfit, values: dict[str, Any]) -> MonthlyIncomeProfit:
    #     v.gross_profit=values["total_sales"] - values["cog"].total_cog
    #     v.ord_income=v.gross_profit-values["sga"].total_sga
    #     return v
    
    def calc_cog(self, mep_base_cost,teaching_cost,ck_cost):
        # print(self.active_st)
        self.cog.class_sess_num=math.ceil(self.active_st/3)*4 #previously 4 stu
        # self.cog.total_reg_teach_cost= self.cog.class_sess_num*teaching_cost
        self.cog.total_reg_teach_cost=self.active_st*math.ceil(teaching_cost/3)*4 #new teaching payment system, 1-3 students = highest teaching cost per stu
        self.cog.total_ck_cost=self.new_st*ck_cost
        self.cog.total_trial_teach_cost=math.ceil(self.new_st*10/3/2)*teaching_cost
        current_mep_inc_ratio = mep_base_ratio + (self.active_st // mep_and_others_inc_threshold) * mep_inc_ratio
        self.cog.mep_cost = mep_base_cost*current_mep_inc_ratio
        if(self.active_st<=49):
            self.cog.royalty_cost = self.total_sales*royalty_ratio[0]
        elif(self.active_st<=99):
            self.cog.royalty_cost = self.total_sales*royalty_ratio[1]
        else:
            self.cog.royalty_cost = self.total_sales*royalty_ratio[2]
        self.cog.total_cog = self.cog.total_reg_teach_cost + self.cog.total_trial_teach_cost + self.cog.total_ck_cost + self.cog.mep_cost + self.cog.royalty_cost
        return self.cog.total_cog

    def calc_sga(self,marketing_cost,admin_cost,others,fixed_asset_cost,bm_cost=0,ruko_rent=0):
        self.sga.marketing_cost=marketing_cost
        self.sga.admin_cost=admin_cost
        current_others_inc_ratio = mep_base_ratio + (self.active_st // mep_and_others_inc_threshold) * others_inc_ratio
        self.sga.others_cost=others*current_others_inc_ratio
        # if ruko_rent:
        self.sga.ruko_rent=ruko_rent
        # if bm_cost:
        self.sga.bm_cost=bm_cost
        self.sga.fixed_asset_cost=fixed_asset_cost
        self.sga.total_sga=self.sga.marketing_cost+self.sga.admin_cost+self.sga.others_cost+self.sga.ruko_rent+self.sga.bm_cost+self.sga.fixed_asset_cost
        return self.sga.total_sga
    
    def calc_vp_sga(self,ruko_rent,additional_rennovation):
        self.vp_sga.ruko_rent=ruko_rent
        self.vp_sga.additional_rennovation=additional_rennovation
        self.vp_sga.total_vp_sga=self.vp_sga.ruko_rent+self.vp_sga.additional_rennovation
        return self.vp_sga.total_vp_sga
        
        
    def calc_profit(self, prev_cum_profit,prev_partner_cum_profit):
        self.profit.gross_profit=self.total_sales - self.cog.total_cog
        self.profit.ord_income=self.profit.gross_profit-self.sga.total_sga
        self.profit.cum_profit=prev_cum_profit+self.profit.ord_income
        self.profit.partner_profit=self.cog.royalty_cost-self.vp_sga.total_vp_sga #untuk vp
        self.profit.partner_cum_profit=prev_partner_cum_profit+self.profit.partner_profit

        
        
class LoginItem(BaseModel):
    username: str
    password: str

    # @app.get("/")
    # def read_root():
    #  return {"Hello": "World"}

@app.post("/login")
async def user_login(loginitem:LoginItem):


    data = jsonable_encoder(loginitem)

    if data['username'] in users and data['password'] == users[data['username']]:

        encoded_jwt = jwt.encode(data, SECERT_KEY, algorithm=ALGORITHM)
        return {"token": encoded_jwt}

    else:
        return {"message":"login failed"}
    
@app.get("/")
def read_root():
    return {"Hello": "World"}


# @app.get("/items/{item_id}")
# def read_item(item_id: int, q: Union[str, None] = None):
#     return {"item_id": item_id, "q": q}


@app.post("/count-sales/")
def read_item(init:InitRequest,response_model=List[MonthlySales]):
    initInvestment=0
    if(init.investment_type=='vp'):
        initInvestment = {
            "mep": init.mep,
            "off_facility": init.off_facility,
            "off_renov": init.off_renov,
            "ruko_rent": init.ruko_rent,
        }
    elif(init.investment_type=='fc'):
        initInvestment = {
            "mep": init.mep,
            "off_facility": init.off_facility,
            "off_renov": init.off_renov,
            "ruko_rent": init.ruko_rent,
            "t_material": init.t_material,
            "license_fee":init.license_fee
        }
    total_invest=-sum(initInvestment.values())
    total_expenses=0
    total_revenue=0
    total_cum_profit=0
    monthly_cog=0
    monthly_sga=0
    vp_sga=0
    sales_list=[]
    fixed_asset_actual_added_times=0
    for i in range(0,60):
        monthly_sga_add_fixed_asset=False
        if i==0:
            m_sales=MonthlySales(
                month=i+1,
                new_st=init.new_st,
                active_st=init.new_st,
                drop_st=0,
                c_price=init.class_price,
                ckit_price=init.ckit_price,
                c_sales=init.new_st*init.class_price*payment_rate,
                ckit_sales=init.new_st*init.ckit_price
            )
            monthly_cog=m_sales.calc_cog(mep_base_cost=init.mep_monthly,teaching_cost=init.teaching_cost,ck_cost=init.ck_cost)
            if(init.investment_type=='vp'):
                monthly_sga=m_sales.calc_sga(admin_cost=init.admin_cost,marketing_cost=init.marketing_cost,ruko_rent=0,others=init.others_cost, fixed_asset_cost=0)
                vp_sga=m_sales.calc_vp_sga(ruko_rent=0,additional_rennovation=0)#sudah dihitung di total invest partner_cum_profit
                m_sales.calc_profit(-init.t_material,prev_partner_cum_profit=total_invest)
            elif(init.investment_type=='fc'):
                monthly_sga=m_sales.calc_sga(admin_cost=init.admin_cost,marketing_cost=init.marketing_cost,ruko_rent=0,others=init.others_cost, fixed_asset_cost=0)
                vp_sga=m_sales.calc_vp_sga(ruko_rent=0,additional_rennovation=0)
                m_sales.calc_profit(total_invest,prev_partner_cum_profit=0)
        else:
            cr_act_st=sales_list[i-1].active_st+init.new_st
            if(cr_act_st>=init.max_st*0.75):
                cr_drop_st=math.ceil(sales_list[i-1].active_st*(drop_rate+0.01))
            else:
                cr_drop_st=math.ceil(sales_list[i-1].active_st*drop_rate)

            if(cr_act_st-cr_drop_st>=init.max_st):
                cr_drop_st+=(cr_act_st-cr_drop_st)-init.max_st

            cr_act_st=cr_act_st-cr_drop_st
            m_sales=MonthlySales(
                month=i+1,
                new_st=init.new_st,
                drop_st=cr_drop_st,
                active_st=cr_act_st,
                c_price=init.class_price,
                ckit_price=init.ckit_price,
                c_sales=cr_act_st*init.class_price*payment_rate,
                ckit_sales=init.new_st*init.ckit_price
            )
            fixed_asset_added_times = m_sales.active_st // fixed_asset_inc_threshold
            if(fixed_asset_actual_added_times<fixed_asset_added_times):
                # asset added
                fixed_asset_actual_added_times+=1
                monthly_sga_add_fixed_asset=True
            # m_sales.profit.cum_profit=sales_list[i-1].profit.cum_profit+m_sales.profit.ord_income
            monthly_cog=m_sales.calc_cog(mep_base_cost=init.mep_monthly,teaching_cost=init.teaching_cost,ck_cost=init.ck_cost)
            fixed_asset_cost=  init.t_material*fixed_asset_inc_ratio if monthly_sga_add_fixed_asset else 0

            if i%12==0:
                if(init.investment_type=='vp'):
                    monthly_sga=m_sales.calc_sga(admin_cost=init.admin_cost,marketing_cost=init.marketing_cost,ruko_rent=0,others=init.others_cost,fixed_asset_cost=fixed_asset_cost)
                    vp_sga=m_sales.calc_vp_sga(ruko_rent=init.ruko_rent,additional_rennovation=0)
                elif(init.investment_type=='fc'):
                    monthly_sga=m_sales.calc_sga(admin_cost=init.admin_cost,marketing_cost=init.marketing_cost,ruko_rent=init.ruko_rent,others=init.others_cost,fixed_asset_cost=fixed_asset_cost)
                    vp_sga=m_sales.calc_vp_sga(ruko_rent=0,additional_rennovation=0)
            else:
                monthly_sga=m_sales.calc_sga(admin_cost=init.admin_cost,marketing_cost=init.marketing_cost,ruko_rent=0,others=init.others_cost,fixed_asset_cost=fixed_asset_cost)
                vp_sga=m_sales.calc_vp_sga(ruko_rent=0,additional_rennovation=0)
            m_sales.calc_profit(sales_list[i-1].profit.cum_profit,prev_partner_cum_profit=sales_list[i-1].profit.partner_cum_profit)

        if(init.investment_type=='vp'):
            total_expenses+=vp_sga
        elif(init.investment_type=='fc'):
            total_expenses+=monthly_cog+monthly_sga
        total_revenue+=m_sales.total_sales
        sales_list.append(m_sales)
    
    if(init.investment_type=='vp'):
        total_cum_profit=sales_list[59].profit.partner_cum_profit
    elif(init.investment_type=='fc'):
        total_cum_profit+=sales_list[59].profit.cum_profit
    responses={
        "investment_type":init.investment_type,
        "monthly_sales":sales_list,
        "total_investment":total_invest*-1,
        "init_investment":initInvestment,
        "total_expenses":total_expenses,
        "total_revenue":total_revenue,
        "total_cum_profit": total_cum_profit
    }
    return responses


# if __name__ == "__main__":
#     import uvicorn
#     uvicorn.run(app, host="127.0.0.1", port=8000)


if __name__ == "__main__":
  uvicorn.run("app", host="0.0.0.0", port=8000, reload=True)